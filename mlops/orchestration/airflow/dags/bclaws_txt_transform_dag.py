import os
from bs4 import BeautifulSoup
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

# ================================
# Constants and Configuration Setup
# ================================

BASE_PATH = "/opt/airflow/"
HTML_DIR = "data/bclaws/html"
TXT_DIR = "data/bclaws/txt"

RETRY_CONFIG = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 9, 11),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': RETRY_CONFIG["retries"],
    'retry_delay': RETRY_CONFIG["retry_delay"],
}

# ================================
# Define the DAG
# ================================
dag = DAG(
    'bclaws_txt_transform_dag',
    default_args=default_args,
    description='A DAG to convert HTML files to plain text',
    schedule_interval=None,  # Triggered by the transformation DAG
    catchup=False,
    tags=['bclaws', 'transformation'],
)

# ================================
# Transformation Functions
# ================================

def convert_html_to_text():
    """Converts all HTML files in the HTML_DIR to plain text and saves them in the TXT_DIR, maintaining folder structure."""
    input_folder = os.path.join(BASE_PATH, HTML_DIR)
    output_folder = os.path.join(BASE_PATH, TXT_DIR)
    
    os.makedirs(output_folder, exist_ok=True)

    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith('.html'):
                input_file_path = os.path.join(root, filename)

                # Calculate relative path to maintain the folder structure
                relative_path = os.path.relpath(root, input_folder)
                output_subfolder = os.path.join(output_folder, relative_path)
                os.makedirs(output_subfolder, exist_ok=True)

                output_file_path = os.path.join(output_subfolder, filename.replace('.html', '.txt'))

                with open(input_file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text()

                # Clean up the text
                cleaned_text = '\n'.join(line.strip() for line in text.splitlines())

                with open(output_file_path, 'w', encoding='utf-8') as file:
                    file.write(cleaned_text)

                print(f'Converted {input_file_path} to plain text at {output_file_path}.')

# ================================
# Task Definitions
# ================================

convert_html_to_text_task = PythonOperator(
    task_id='convert_html_to_text',
    python_callable=convert_html_to_text,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# #Trigger the S3 upload DAG after transformations finish
# trigger_s3_upload = TriggerDagRunOperator(
#     task_id='trigger_upload_to_s3',
#     trigger_dag_id='upload_data_to_s3_dag',  # Name of the DAG to trigger
#     wait_for_completion=False,               # Do not wait for the upload DAG to complete
#     trigger_rule='all_success',              # Trigger S3 upload only if the scraper succeeds completely
#     dag=dag
# )

# Set up basic one-task DAG
convert_html_to_text_task

# trigger_s3_upload
