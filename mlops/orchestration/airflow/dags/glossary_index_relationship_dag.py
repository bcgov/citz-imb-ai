import os
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from langchain_community.graphs import Neo4jGraph
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import boto3
import os
from dotenv import load_dotenv
load_dotenv("/vault/secrets/zuba-secret-dev")


## STEP 1 - Download Glossary from S3
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')

linode_obj_config = {
    "aws_access_key_id": S3_ACCESS_KEY,
    "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}
bucket_name = "IMBAIPilot"

def download_data(bucket, path, bucket_name):
    prefix = bucket
    client = boto3.client("s3", **linode_obj_config)
    BASE_PATH = path
    if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH, mode=0o777)
    
    continuation_token = None

    while True:
        if continuation_token:
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, ContinuationToken=continuation_token)
        else:
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' in response:
            for obj in response['Contents']:
                newpath = os.path.join(BASE_PATH, obj['Key'].split('/')[-1])
                if newpath != path:
                    print(newpath)
                    client.download_file(bucket_name, obj['Key'], newpath)

        # Check if more pages are available
        if response.get('IsTruncated'):  # If the response is truncated, there are more pages to retrieve
            continuation_token = response.get('NextContinuationToken')
        else:
            break

def download_glossary():
    download_data("bclaws/glossary", "JSON_glossary/", bucket_name)


## STEP 2 - Index Glossary
NEO4J_URI = 'bolt://' + os.getenv('NEO4J_HOST') + ':7687'
NEO4J_USERNAME = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DB')

kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)

cypher = """
  MATCH (n) 
  RETURN count(n)
  """
result = kg.query(cypher)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap  = 200,
    length_function = len,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# need to ensure that the glossary.json file is available
f = open('/opt/airflow/dags/JSON_glossary/glossary.json')
glossaries = json.load(f)

token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=20, tokens_per_chunk=256)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def create_index():
    merge_chunk_node_query = """
    MERGE(mergedChunk:UpdatedChunk {chunkId: $chunkParam.chunkId})
        ON CREATE SET 
            mergedChunk.chunkSeqId = $chunkParam.chunkSeqId, 
            mergedChunk.text = $chunkParam.text,
            mergedChunk.type = $chunkParam.type,
            mergedChunk.url = $chunkParam.url,
            mergedChunk.glossaryTerm = $chunkParam.glossaryTerm
    RETURN mergedChunk
    """

    create_embeddings = """
            MATCH (chunk:UpdatedChunk) WHERE
            chunk.chunkId = $chunkParam.chunkId
            AND chunk.chunkSeqId = $chunkParam.chunkSeqId
            AND chunk.text = $chunkParam.text
            AND chunk.type = $chunkParam.type
            AND chunk.url = $chunkParam.url
            AND chunk.glossaryTerm = $chunkParam.glossaryTerm
            AND chunk.textEmbedding is NULL
            CALL db.create.setNodeVectorProperty(chunk, "textEmbedding", $vector)
            RETURN chunk
        """
    for glossary in enumerate(glossaries['terms']):
        text = glossary[1]['term'] + ': ' + glossary[1]['description']
        token_split_texts = []
        data_type = 'glossary'
        # Validate if all the text fits into the 256 token size to create the embeddings
        token_split_texts += token_splitter.split_text(text)
        # create meta data
        for chunk_seq, token in enumerate(token_split_texts):
            chunk = {
                'type': data_type,
                'text': token,
                'chunkSeqId': chunk_seq,
                'chunkId': f'{data_type}-{glossary[1]["term"]}-seq-{str(chunk_seq)}',
                'url': 'https://www.bclaws.gov.bc.ca/glossary.html',
                'glossaryTerm': glossary[1]['term']
            }
            kg.query(merge_chunk_node_query, 
                params={
                    'chunkParam': chunk
                })
            vector = embeddings.embed_query(chunk['text'])
            result = kg.query(create_embeddings, params={'chunkParam':chunk, 'vector':vector})


##STEP 3 - Create Edges
def connect_chunks():
    connect_chunks = """
      MATCH (chunk:UpdatedChunk), (f:UpdatedChunk)
      WHERE
        chunk.chunkId = $chunkParam.chunkId
        AND chunk.chunkSeqId = $chunkParam.chunkSeqId
        AND chunk.text = $chunkParam.text
        AND chunk.glossaryTerm = $chunkParam.glossaryTerm1
        AND chunk.type = $chunkParam.type
        AND f.type = $chunkParam.type
        AND f.glossaryTerm = $chunkParam.glossaryTerm2
        AND f.chunkId = $chunkParam.chunkId2
        AND f.chunkSeqId = 0
      MERGE (chunk)-[newRelationship:RELATED_TERMS]->(f)
      RETURN count(newRelationship)
    """
    for idx, glossary in enumerate(glossaries['terms']):
        text = glossary['term'] + ': ' + glossary['description']
        token_split_texts = []
        data_type = 'glossary'
        
        # Split text into chunks fitting the 256 token size
        token_split_texts += token_splitter.split_text(text)
        
        for chunk_seq, token in enumerate(token_split_texts):
            for glossary_term in glossary['related_terms']:
                chunk = {
                    'type': data_type,
                    'text': token,
                    'chunkSeqId': chunk_seq,
                    'chunkId': f'{data_type}-{glossary["term"]}-seq-{chunk_seq}',
                    'url': 'https://www.bclaws.gov.bc.ca/glossary.html',
                    'glossaryTerm1': glossary['term'],
                    'glossaryTerm2': glossary_term,
                    'chunkId2': f'{data_type}-{glossary_term}-seq-0'  # Assuming seq-0 for related terms
                }
                
                # Execute the query with the current chunk parameters
                ret = kg.query(connect_chunks, params={'chunkParam': chunk})
                print(chunk)
                print(ret)
                print('\n\n')

## CREATE DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 7, 25),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'glossary_indexing_and_relationships',
    default_args=default_args,
    description='A DAG to index the BC Laws glossary and create relationships in Neo4j',
    schedule_interval=timedelta(days=1),
) as dag:
    download_glossary_from_s3 = PythonOperator(
        task_id='download_glossary_from_s3',
        python_callable=download_glossary,
        dag=dag,
    )
    index_glossary = PythonOperator(
        task_id='index_glossary',
        python_callable=create_index,
        dag=dag,
    )
    create_glossary_relationships = PythonOperator(
        task_id='create_glossary_relationships',
        python_callable=connect_chunks,
        dag=dag,
    )


download_glossary_from_s3 >> index_glossary >> create_glossary_relationships