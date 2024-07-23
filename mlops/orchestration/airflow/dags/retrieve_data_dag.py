from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
import boto3
import os
from dotenv import load_dotenv

load_dotenv("/vault/secrets/zuba-secret-dev")
# Set environment variables
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')

print(S3_ACCESS_KEY)
print(S3_ENDPOINT_URL)
print(S3_SECRET_ACCESS_KEY)

linode_obj_config = {
    "aws_access_key_id": S3_ACCESS_KEY,
    "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}
bucket_name = "IMBAIPilot"

def download_data(bucket, path, bucket_name):
    prefix = bucket
    client = boto3.client("s3", **linode_obj_config)
    print(client)
    BASE_PATH = path
    if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH, mode=0o777)
    
    continuation_token = None

    while True:
        if continuation_token:
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, ContinuationToken=continuation_token)
        else:
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            print(response)
        
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

def download_bclaws_acts():
    download_data("bclaws/data/xml/Cleaned/Acts", "XML_Acts/", bucket_name)

def download_bclaws_regulations():
    download_data("bclaws/data/xml/Cleaned/Regulations", "XML_Regulations/", bucket_name)

def download_bclaws_glossary():
    download_data("bclaws/glossary", "JSON_glossary/", bucket_name)

def download_ticket_graphicdata():
    download_data("bclaws/data_v2/OCR/", "JSON_graphicdata/", bucket_name)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    'retrieve_data_from_s3_dag',
    default_args=default_args,
    description='Retrieve B.C. laws data from S3',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['bclaws', 's3'],
) as dag:

    task_download_acts = PythonOperator(
        task_id='download_bclaws_acts',
        python_callable=download_bclaws_acts,
    )

    task_download_regulations = PythonOperator(
        task_id='download_bclaws_regulations',
        python_callable=download_bclaws_regulations,
    )
    
    task_download_glossary = PythonOperator(
        task_id='download_bclaws_glossary',
        python_callable=download_bclaws_glossary,
    )

    task_download_graphicdata = PythonOperator(
        task_id='download_ticket_graphicdata',
        python_callable=download_ticket_graphicdata,
    )

    task_download_acts >> task_download_regulations >> task_download_glossary >> task_download_graphicdatafrom airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
import boto3
import os
from dotenv import load_dotenv

load_dotenv("/vault/secrets/zuba-secret-dev")
# Set environment variables
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')

print(S3_ACCESS_KEY)
print(S3_ENDPOINT_URL)
print(S3_SECRET_ACCESS_KEY)

linode_obj_config = {
    "aws_access_key_id": S3_ACCESS_KEY,
    "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}
bucket_name = "IMBAIPilot"

def download_data(bucket, path, bucket_name):
    prefix = bucket
    client = boto3.client("s3", **linode_obj_config)
    print(client)
    BASE_PATH = path
    if not os.path.exists(BASE_PATH): os.makedirs(BASE_PATH, mode=0o777)
    
    continuation_token = None

    while True:
        if continuation_token:
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, ContinuationToken=continuation_token)
        else:
            response = client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            print(response)
        
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

def download_bclaws_acts():
    download_data("bclaws/data/xml/Cleaned/Acts", "XML_Acts/", bucket_name)

def download_bclaws_regulations():
    download_data("bclaws/data/xml/Cleaned/Regulations", "XML_Regulations/", bucket_name)

def download_bclaws_glossary():
    download_data("bclaws/glossary", "JSON_glossary/", bucket_name)

def download_ticket_graphicdata():
    download_data("bclaws/data_v2/OCR/", "JSON_graphicdata/", bucket_name)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

with DAG(
    'retrieve_data_from_s3_dag',
    default_args=default_args,
    description='Retrieve B.C. laws data from S3',
    schedule_interval='@daily',
    start_date=days_ago(1),
    catchup=False,
    tags=['bclaws', 's3'],
) as dag:

    task_download_acts = PythonOperator(
        task_id='download_bclaws_acts',
        python_callable=download_bclaws_acts,
    )

    task_download_regulations = PythonOperator(
        task_id='download_bclaws_regulations',
        python_callable=download_bclaws_regulations,
    )
    
    task_download_glossary = PythonOperator(
        task_id='download_bclaws_glossary',
        python_callable=download_bclaws_glossary,
    )

    task_download_graphicdata = PythonOperator(
        task_id='download_ticket_graphicdata',
        python_callable=download_ticket_graphicdata,
    )

    task_download_acts >> task_download_regulations >> task_download_glossary >> task_download_graphicdata
