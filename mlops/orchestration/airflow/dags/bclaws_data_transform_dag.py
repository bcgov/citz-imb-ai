# # Step 5: Trigger the S3 upload DAG after transformations finish
# trigger_s3_upload = TriggerDagRunOperator(
#     task_id='trigger_upload_to_s3',
#     trigger_dag_id='upload_data_to_s3_dag',  # Name of the DAG to trigger
#     wait_for_completion=False,               # Do not wait for the upload DAG to complete
#     trigger_rule='all_success',              # Trigger S3 upload only if the scraper succeeds completely
#     dag=dag
# )
# ### ###

# # =======================
# # Set Up Task Dependencies
# # =======================

# trigger_s3_upload 




import os
import re
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

# ================================
# Constants and Configuration Setup
# ================================

# Directory paths for where files are stored
BASE_PATH = "/opt/airflow/"
HTML_DIR = "data/bclaws/html"
XML_DIR = "data/bclaws/xml"

# Retry behavior configuration for tasks in the transformation
RETRY_CONFIG = {
    "retries": 3,  # Retry up to 3 times for each task
    "retry_delay": timedelta(minutes=5),  # Wait 5 minutes between retries
}

# Default arguments configuration for the DAG
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
    'bclaws_data_transform_dag',
    default_args=default_args,
    description='A DAG to transform downloaded BC Laws HTML data',
    schedule_interval=None,  # This will be triggered externally, like in the Scraper DAG
    catchup=False,
    tags=['bclaws', 'transformation'],
)

# ================================
# Transformation Functions (One per Task)
# ================================

def handle_unicode_errors():
    """Handle Unicode errors in all HTML files by replacing invalid characters."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                file_path = os.path.join(root, filename)
                try:
                    # Open the file, replace invalid Unicode characters, and save it back
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                        content = file.read()

                    # Save the cleaned content back to the file
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    print(f'Repaired Unicode in {filename} in {root}')
                
                except Exception as e:
                    print(f"Failed to handle Unicode for {file_path}: {e}")


def prettify_html_files():
    """Recursively prettify all HTML files in the root and subdirectories."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Prettify content
                formatter = HTMLFormatter(indent=3)
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.prettify(formatter=formatter)

                # Save prettified content back to the same file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f'Prettified {filename} in {root}')


def remove_unwanted_tags():
    """Remove unwanted tags and attributes from all HTML files in the root and subdirectories."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Remove unwanted tags and attributes
                content = re.sub(r'<\?xml version="1.0" encoding="UTF-8"\?>', '', content, flags=re.DOTALL)
                content = re.sub(r'<!DOCTYPE html[^>]*>', '', content)
                content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL)
                content = re.sub(r'<html[^>]*>', '<html>', content)
                content = re.sub(r'<body[^>]*>', '<body>', content)
                content = re.sub(r'<div id="toolBar"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
                content = re.sub(r'<div id="header"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
                content = re.sub(r'<div id="act:currency"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
                content = re.sub(r'<div id="contents"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
                content = re.sub(r'<p class="copyright"[^>]*>.*?</p>', '', content, flags=re.DOTALL)

                # Save cleaned content back to the same file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f'Tags removed from {filename} in {root}')


def final_prettify():
    """Do a final prettification of all HTML files in the root and subdirectories."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Final prettification
                formatter = HTMLFormatter(indent=3)
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.prettify(formatter=formatter)

                # Save prettified content back to the same file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f'Final prettification done for {filename} in {root}')


# ================================
# Task Definitions
# ================================

handle_unicode_errors_task = PythonOperator(
    task_id='handle_unicode_errors',
    python_callable=handle_unicode_errors,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

prettify_html_task = PythonOperator(
    task_id='prettify_html',
    python_callable=prettify_html_files,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

remove_unwanted_tags_task = PythonOperator(
    task_id='remove_unwanted_tags',
    python_callable=remove_unwanted_tags,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

final_prettify_task = PythonOperator(
    task_id='final_prettify',
    python_callable=final_prettify,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# ================================
# Set Up Task Dependencies
# ================================

# Fix Unicode errors -> Prettify -> Remove Tags -> Final Prettification
handle_unicode_errors_task >> prettify_html_task >> remove_unwanted_tags_task >> final_prettify_task
