from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
import boto3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load secret environment variables for S3 access
load_dotenv("/vault/secrets/zuba-secret-dev")

S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
bucket_name = "IMBAIPilot"

# Configuration for the S3 client
linode_obj_config = {
    "aws_access_key_id": S3_ACCESS_KEY,
    "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}

# Function to upload a single file to S3 under the timestamped folder
def upload_to_s3(file_path, bucket_name, key_prefix="", client=None):
    """Upload a given file to the S3 bucket under a key prefix (directory in S3)."""
    if client is None:
        client = boto3.client("s3", **linode_obj_config)  # Initialize the S3 client if not already provided
    
    file_name = os.path.basename(file_path)  # Determine the filename from the file_path
    s3_key = f"{key_prefix}{file_name}"     # Full S3 key (path inside the bucket)

    # Upload the file to the specified S3 bucket and key
    client.upload_file(file_path, bucket_name, s3_key)
    print(f"Uploaded {file_name} to {bucket_name}/{s3_key}")

# Function to perform the actual upload from the bclaws directory to S3
def upload_bclaws_to_s3():
    """Upload all files and subfolders from the 'bclaws' directory to S3, under a timestamp folder."""
    base_dir = os.path.join("/opt/airflow/", "data/bclaws/")  # Root directory where scraper stores files

    # Generate the desired timestamp format (e.g., "2024_10_10-11_30_00PM")
    timestamp = datetime.utcnow().strftime('%Y_%m_%d-%I_%M_%S%p')  # Format for the folder (12-hour clock with AM/PM)
    
    # The key prefix will include the timestamp to create a unique folder in S3
    root_key_prefix = f"bclaws/{timestamp}/"

    client = boto3.client("s3", **linode_obj_config)  # Initialize S3 client
    
    # Walk through the local directory to find files for upload
    for root, dirs, files in os.walk(base_dir):
        relative_path = os.path.relpath(root, base_dir)  # Relative path (subfolder structure) inside the base folder
        if relative_path == ".":  # Root folder of base_dir eliminated from key prefix
            relative_path = ""    # No relative path at root

        # Generate the S3 key prefix including the relative folder structure
        upload_prefix = f"{root_key_prefix}{relative_path}/"

        # Upload each file found in the directory
        for file_name in files:
            file_path = os.path.join(root, file_name)  # Absolute local file path
            upload_to_s3(file_path, bucket_name, key_prefix=upload_prefix, client=client)

# Define the DAG's default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG that gets triggered to upload contents to S3
with DAG(
    'upload_data_to_s3_dag',                      # DAG ID for S3 Upload
    default_args=default_args,                    # DAG default settings
    description='Upload B.C. laws data to S3 from bclaws directory into a timestamped folder',
    schedule_interval=None,                       # This DAG is triggered manually
    start_date=days_ago(1),
    catchup=False,
    tags=['upload', 's3', 'bclaws'],
) as dag:

    # Task to upload all files from the scraper's bclaws directory to S3
    task_upload_to_s3 = PythonOperator(
        task_id='upload_files_to_s3',
        python_callable=upload_bclaws_to_s3,        # Call the S3 upload logic
        execution_timeout=timedelta(hours=1),       # Set a timeout for this upload
    )

    task_upload_to_s3  # Dummy definition for this standalone task