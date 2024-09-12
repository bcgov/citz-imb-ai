from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
import boto3
import os
import shutil
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/vault/secrets/zuba-secret-dev")

# S3 configuration
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
bucket_name = "IMBAIPilot"

# S3 client configuration
linode_obj_config = {
    "aws_access_key_id": S3_ACCESS_KEY,
    "aws_secret_access_key": S3_SECRET_ACCESS_KEY,
    "endpoint_url": S3_ENDPOINT_URL,
}

# DAG default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'start_date': datetime(2024, 9, 11),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'upload_data_to_s3_dag',
    default_args=default_args,
    description='Upload B.C. laws data to S3 from bclaws directory into a timestamped folder',
    schedule_interval=None,  # Manual trigger
    catchup=False,
    tags=['upload', 's3', 'bclaws'],
)

# ==========================
# Task Logic - Upload to S3
# ==========================

def check_for_data():
    """Check if 'bclaws' folder has data."""
    base_dir = os.path.join("/opt/airflow/", "data/bclaws/")
    
    # Return False if directory is empty
    if not any(os.scandir(base_dir)):
        print(f"No data found in {base_dir}. Skipping the upload...")
        return False

    print(f"Data found in {base_dir}. Proceeding with the DAG.")
    return True


def upload_to_s3(file_path, bucket_name, key_prefix="", client=None):
    """Upload file to S3 bucket."""
    # Initialize S3 client if not provided
    if client is None:
        client = boto3.client("s3", **linode_obj_config)
    
    file_name = os.path.basename(file_path)
    s3_key = f"{key_prefix}{file_name}"

    # Perform upload
    client.upload_file(file_path, bucket_name, s3_key)
    print(f"Uploaded {file_name} to {bucket_name}/{s3_key}")


def upload_bclaws_to_s3():
    """Upload 'bclaws' directory contents to S3."""
    base_dir = os.path.join("/opt/airflow/", "data/bclaws/")

    # Create timestamped folder name
    timestamp = datetime.utcnow().strftime('%Y_%m_%d-%I_%M_%S%p')
    root_key_prefix = f"bclaws/{timestamp}/"

    client = boto3.client("s3", **linode_obj_config)
    
    # Traverse directory and upload files
    for root, dirs, files in os.walk(base_dir):
        relative_path = os.path.relpath(root, base_dir)
        relative_path = "" if relative_path == "." else relative_path

        upload_prefix = f"{root_key_prefix}{relative_path}/"

        # Upload each file in current directory
        for file_name in files:
            file_path = os.path.join(root, file_name)
            upload_to_s3(file_path, bucket_name, key_prefix=upload_prefix, client=client)            

    print(f"Data successfully uploaded to S3 at '{root_key_prefix}'.")


def clean_bclaws_folder():
    """Remove all contents from 'bclaws' folder."""
    base_dir = os.path.join("/opt/airflow/", "data/bclaws/")
    
    # Delete files and subdirectories
    for root, dirs, files in os.walk(base_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            shutil.rmtree(dir_path)
            print(f"Deleted directory: {dir_path}")

    print(f"All contents of {base_dir} have been deleted.")

# ==========================
# Task Definitions
# ==========================

# Check for data presence
check_for_data_task = PythonOperator(
    task_id='check_for_data',
    python_callable=lambda: check_for_data() or False,
    dag=dag,
)

# Dummy task for no data scenario
no_data_task = DummyOperator(
    task_id='no_data_found',
    dag=dag,
)

# Upload files to S3
upload_to_s3_task = PythonOperator(
    task_id='upload_files_to_s3',
    python_callable=upload_bclaws_to_s3,
    execution_timeout=timedelta(hours=1),
    dag=dag,
)

# Clean up after successful upload
clean_bclaws_task = PythonOperator(
    task_id='clean_bclaws_folder',
    python_callable=clean_bclaws_folder,
    execution_timeout=timedelta(minutes=30),
    dag=dag,
)

# ==========================
# Task Dependencies
# ==========================

# Execute upload or skip based on data presence
check_for_data_task >> [upload_to_s3_task, no_data_task]

# Clean up only after successful upload
upload_to_s3_task >> clean_bclaws_task
