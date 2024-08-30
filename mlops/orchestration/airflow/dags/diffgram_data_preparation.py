from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
import random
import os
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv
import tarfile
import boto3
import json

load_dotenv("/vault/secrets/zuba-secret-dev")

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

linode_obj_config = {
    "aws_access_key_id": S3_ACCESS_KEY,
    "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}
s3_bucket = "IMBAIPilot"
# Generate a unique object key
object_key = f"diffgram_processing/rar/diffgram_processing_{datetime.now().strftime('%Y%m%d%H%M%S')}.tar.gz"


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

output_dir = "/opt/airflow/diffgram_processing"


# Save the Neo4j query result to a file
def query_neo4j():
    cypher = """
    MATCH (n:UpdatedChunk) 
    RETURN n.sectionName, n.ActId as ActId, n.RegId as RegId,  n.sectionId as sectionId, n.sectionName as sectionName, n.chunkId as chunkId, n.text as text, n.chunkSeqId as seqId
    """
    neo4j_dump = kg.query(cypher)
    # Save the result to a file
    with open("/opt/airflow/neo4j_dump.json", "w") as f:
        json.dump(neo4j_dump, f)

    print(f"Neo4j data has been dumped")


# Process and save chunks from the query result file
def process_and_save_chunks_from_file():
    if not os.path.exists("/opt/airflow/neo4j_dump.json"):
        print("No data to process")
        return

    result = json.load(open("/opt/airflow/neo4j_dump.json"))
    random.shuffle(result)

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for index, entry in enumerate(result):
        chunk_id = entry["chunkId"]
        actId = entry["ActId"]
        regId = entry["RegId"]
        sectionName = entry["sectionName"]
        sectionId = entry["sectionId"]
        seqId = entry["seqId"]
        text = entry["text"]

        output_file = os.path.join(output_dir, f"{index}.txt")

        output_text = (
            f"Chunk ID: {chunk_id}\n"
            f"Act ID: {actId}\n"
            f"Regulation ID: {regId}\n"
            f"Section Name: {sectionName}\n"
            f"Section ID: {sectionId}\n"
            f"Sequence ID: {seqId}\n"
            f"Text:\n{text}\n"
        )

        with open(output_file, "w") as f:
            f.write(output_text)

    print(f"Processed and shuffled data has been written to the folder: {output_dir}")


# Function to create a tar.gz archive of the output directory
def create_tar_gz():
    tar_file = "/opt/airflow/diffgram_processing.tar.gz"
    with tarfile.open(tar_file, "w:gz") as tar:
        tar.add(output_dir, arcname=os.path.basename(output_dir))
    print(f"Created tar.gz archive: {tar_file}")
    return tar_file


# Function to upload the tar.gz file to S3
def upload_to_s3():
    tar_file = "/opt/airflow/diffgram_processing.tar.gz"
    client = boto3.client("s3", **linode_obj_config)
    client.upload_file(tar_file, s3_bucket, object_key)
    print(f"Uploaded {tar_file} to s3://{s3_bucket}{object_key}")


# Define the default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

# Define the DAG
with DAG(
    "diffgram_data_preparation",
    default_args=default_args,
    description="A DAG to query Neo4j, process data, and save it to files",
    schedule_interval=None,
    catchup=False,
) as dag:

    # Task to query Neo4j and save result to a file
    query_neo4j_task = PythonOperator(
        task_id="query_neo4j",
        python_callable=query_neo4j,
    )

    # Task to process and save chunks from the query result file
    process_and_save_chunks_task = PythonOperator(
        task_id="process_and_save_chunks_from_file",
        python_callable=process_and_save_chunks_from_file,
    )

    # Task to create tar.gz archive
    create_tar_gz_task = PythonOperator(
        task_id="create_tar_gz",
        python_callable=create_tar_gz,
    )

    # Task to upload tar.gz archive to S3
    upload_to_s3_task = PythonOperator(
        task_id="upload_to_s3",
        python_callable=upload_to_s3,
    )

    # Define the task dependencies
    (
        query_neo4j_task
        >> process_and_save_chunks_task
        >> create_tar_gz_task
        >> upload_to_s3_task
    )
