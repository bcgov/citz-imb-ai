from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from dotenv import load_dotenv

import os
from bs4 import BeautifulSoup
from langchain_community.graphs import Neo4jGraph
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
import warnings
from langchain_community.document_loaders import DirectoryLoader
from llama_index.core import SimpleDirectoryReader, StorageContext
warnings.filterwarnings("ignore")
from langchain_community.embeddings import HuggingFaceEmbeddings
from airflow.sensors.external_task_sensor import ExternalTaskSensor
import json

load_dotenv("/vault/secrets/zuba-secret-dev")

def neo4j():
    NEO4J_URI = "bolt://citz-imb-ai-neo4j-svc:7687"
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    NEO4J_DB = os.getenv("NEO4J_DB")
    kg = Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DB,
    )
    return kg

kg = neo4j()
    
file_metadata = lambda x: {"filename": x}
def graphic_documents():
    graphic_documents = SimpleDirectoryReader(
        "./JSON_graphicdata/", file_metadata=file_metadata
    ).load_data()
    return graphic_documents

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap  = 200,
    length_function = len,
    separators=["\n\n", "\n", ". ", " ", ""],
)

merge_chunk_node_query = """
MERGE(mergedChunk:UpdatedChunk {chunkId: $chunkParam.chunkId})
    ON CREATE SET 
        mergedChunk.chunkSeqId = $chunkParam.chunkSeqId, 
        mergedChunk.text = $chunkParam.text,
        mergedChunk.ActId = $chunkParam.ActId,
        mergedChunk.sectionName = $chunkParam.sectionName,
        mergedChunk.url = $chunkParam.url,
        mergedChunk.regulationinfo = $chunkParam.regulationinfo,
        mergedChunk.regulationSeqId = $chunkParam.regulationSeqId,
        mergedChunk.parentRetrieval = $chunkParam.parentRetrieval,
        mergedChunk.formtitle = $chunkParam.formtitle,
        mergedChunk.RegId = $chunkParam.RegId
RETURN mergedChunk
"""

create_embeddings = """
        MATCH (chunk:UpdatedChunk) WHERE
        chunk.chunkId = $chunkParam.chunkId
        AND chunk.chunkSeqId = $chunkParam.chunkSeqId
        AND chunk.ActId = $chunkParam.ActId
        AND chunk.sectionName = $chunkParam.sectionName
        AND chunk.text = $chunkParam.text
        AND chunk.regulationinfo = $chunkParam.regulationinfo
        AND chunk.regulationSeqId = $chunkParam.regulationSeqId
        AND chunk.url = $chunkParam.url
        AND chunk.formtitle = $chunkParam.formtitle
        AND chunk.textEmbedding is NULL
        CALL db.create.setNodeVectorProperty(chunk, "textEmbedding", $vector)
        RETURN chunk
    """


def create_chunk_relationship(act_info):
    cypher = """
  MATCH (from_same_section:UpdatedChunk)
  WHERE from_same_section.ActId = $ActParam['ActId']
  AND from_same_section.sectionName = $ActParam['sectionName']
  AND from_same_section.RegId = $ActParam['RegId']
  AND from_same_section.url = $ActParam['url']
  AND from_same_section.formtitle = $ActParam['formtitle']
  AND from_same_section.regulationSeqId = $ActParam['regulationSeqId']
  WITH from_same_section
    ORDER BY from_same_section.chunkSeqId ASC
  WITH collect(from_same_section) as section_chunk_list
    CALL apoc.nodes.link(
        section_chunk_list, 
        "NEXT", 
        {avoidDuplicates: true}
    )  // NEW!!!
  RETURN size(section_chunk_list)
"""
    kg.query(cypher, params={"ActParam": act_info})


def create_chunk_embeddings(tokens, embeddings):
    for chunk in tokens:
        print(f"Creating `:Chunk` node for chunk ID {chunk['chunkSeqId']}")
        kg.query(merge_chunk_node_query, params={"chunkParam": chunk})
        vector = embeddings.embed_query(chunk["text"])
        result = kg.query(
            create_embeddings, params={"chunkParam": chunk, "vector": vector}
        )
        if result:
            print("Embedding created")
        else:
            print(result)
            print("Embedding not created")
    create_chunk_relationship(tokens[0] )


def create_metadata(
    token_split_texts,
    title,
    section_heading,
    regulationinfo,
    url,
    regid,
    seq_id,
    formtitle,
):
    chunks_with_metadata = []  # use this to accumlate chunk records
    chunk_seq_id = 0
    for chunk in token_split_texts:  # only take the first 20 chunks
        # form_id = file[file.rindex('/') + 1:file.rindex('.')] # extract form id from file name
        # finally, construct a record with metadata and the chunk text
        chunks_with_metadata.append(
            {
                "text": chunk,
                # metadata from looping...
                "chunkSeqId": chunk_seq_id,
                "chunkId": f"{title}-{regid}-chunk-{section_heading}-{chunk_seq_id:04d}",
                "ActId": f"{title}",
                "RegId": f"{regid}",
                "sectionName": f"{section_heading}",
                "url": f"{url}",
                "regulationinfo": f"{regulationinfo}",
                "regulationSeqId": seq_id,
                "parentRetrieval": True,
                "formtitle": formtitle,
                # constructed metadata...
                # metadata from file...
            }
        )
        chunk_seq_id += 1
    return chunks_with_metadata


def create_chunks(item_text, title, section_heading, section_id):
    item_text_chunks = text_splitter.split_text(item_text)  # split the text into chunks
    token_splitter = SentenceTransformersTokenTextSplitter(
        chunk_overlap=20, tokens_per_chunk=256
    )
    token_split_texts = []
    for text in item_text_chunks:
        token_split_texts += token_splitter.split_text(text)
    meta_data = create_metadata(token_split_texts, title, section_heading, section_id)
    return meta_data


def index_ticket_graphicdata():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    kg = neo4j()
    for index, graphic_document in enumerate(graphic_documents()):
        # print(json.loads(graphic_document.get_text()))
        json_obj = json.loads(graphic_document.get_text())
        url = json_obj["Url"]
        title = json_obj["Title"]
        regulation_info = json_obj["RegulationInfo"]
        description = json_obj["Description"]
        actid = json_obj["ActId"]
        regid = json_obj["RegulationId"]
        text = json_obj["Text"]
        parent_retrieval = ""
        if len(text):
            # sectionfn(text)
            # break
            for section_index, section in enumerate(text):
                sectiontitle = section["Title"]
                # print(sectiontitle)
                if len(section["Description"]):
                    for subsection_index, subsection in enumerate(
                        section["Description"]
                    ):
                        subsectiontitle = subsection["Title"]
                        subsectiondescription = subsection["Description"]
                        if sectiontitle == subsectiontitle:
                            # print(sectiontitle + ' \n' + subsectiondescription)
                            item_text = sectiontitle + " \n" + subsectiondescription
                            # create_chunks
                        else:
                            item_text = (
                                sectiontitle
                                + ": "
                                + subsectiontitle
                                + " \n"
                                + subsectiondescription
                            )
                            # print(sectiontitle + ': '+ subsectiontitle + ' \n' + subsectiondescription)
                        print("\n\n")
                        item_text_chunks = text_splitter.split_text(
                            item_text
                        )  # split the text into chunks
                        token_splitter = SentenceTransformersTokenTextSplitter(
                            chunk_overlap=20, tokens_per_chunk=256
                        )
                        token_split_texts = []
                        for text in item_text_chunks:
                            token_split_texts += token_splitter.split_text(text)
                        print(token_split_texts)
                        token = create_metadata(
                            token_split_texts,
                            actid,
                            subsectiontitle,
                            regulation_info,
                            url,
                            regid,
                            subsection_index,
                            title,
                        )
                        print(token)
                        create_chunk_embeddings(token, embeddings)
                        parent_retrieval += item_text + "\n\n"


## Creating the parent chunk relationship
#Create Parent Chunk
def create_parent_form_node(form_info):
    cypher = """
        MERGE (mergedChunk:form {formtitle: $chunkParam.Title })
          ON CREATE SET
        mergedChunk.text = $chunkParam.text,
        mergedChunk.url = $chunkParam.url,
        mergedChunk.regulationinfo = $chunkParam.regulationinfo,
        mergedChunk.formtitle = $chunkParam.Title,
        mergedChunk.RegId = $chunkParam.RegId,
        mergedChunk.LawId = $chunkParam.ActId
            """
    kg.query(cypher, params={'chunkParam': form_info})

def connect_form_parentNode():
    cypher = """
      MATCH (c:UpdatedChunk), (f:form)
        WHERE c.formtitle = f.formtitle
        AND c.chunkSeqId = 0
      MERGE (c)-[newRelationship:PARENT]->(f)
      MERGE (f)-[newRelationship2:CHILD]->(c)
      RETURN count(newRelationship)
    """
    kg.query(cypher)


def create_relationships():
    for index, graphic_document in enumerate(graphic_documents()):
        json_obj = json.loads(graphic_document.get_text())
        create_parent_form_node(json_obj)
        connect_form_parentNode()

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
}

with DAG(
    "ticket_graphicdata_indexing",
    default_args=default_args,
    description="Indexing ticket graphic data",
    schedule_interval="@weekly",
    start_date=days_ago(1),
    catchup=False,
    tags=["bclaws", "graphicdata", "indexing"],
) as dag:
    
    wait_for_download = ExternalTaskSensor(
        task_id='wait_for_download_ticket_graphic_data',
        external_dag_id='retrieve_data_from_s3_dag',  # DAG id to wait for
        external_task_id='download_ticket_graphicdata',  # Wait for the entire DAG to complete
        timeout=600,  # Timeout in seconds
        poke_interval=60,  # Check interval in seconds
        mode='poke',  # or 'reschedule'
    )

    task_index_ticket_graphicdata = PythonOperator(
        task_id="index_ticket_graphicdata",
        python_callable=index_ticket_graphicdata,
    )

    task_index_ticket_parent_relationship = PythonOperator(
        task_id="create_relationships",
        python_callable=create_relationships,
    )

    wait_for_download >> task_index_ticket_graphicdata >> task_index_ticket_parent_relationship
