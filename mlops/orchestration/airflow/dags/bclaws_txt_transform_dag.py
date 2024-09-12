import os
import shutil
from bs4 import BeautifulSoup
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
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

dag = DAG(
    'bclaws_txt_transform_dag',
    default_args=default_args,
    description='A DAG to convert HTML files to plain text and remove blank lines in place',
    schedule_interval=None,  # Triggered by the transformation DAG
    catchup=False,
    tags=['bclaws', 'transformation'],
)

# ================================
# Helper Functions
# ================================

def create_folder_if_not_exists(folder_path):
    """Ensure that the folder exists by creating it if necessary."""
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created directory: {folder_path}")
    except Exception as e:
        print(f"Failed to create directory {folder_path}. Reason: {e}")

# ===============================
# Task 1: Clean the Text Folder
# ===============================

def clean_txt_folder():
    """Clean the TXT directory before starting the text conversion."""
    folder = os.path.join(BASE_PATH, TXT_DIR)
    
    # Step 1: Ensure the folder exists, if not, create it
    create_folder_if_not_exists(folder)
    
    # Step 2: If folder exists, clean it
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Deleted directory: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"Folder does not exist: {folder}")
    
    print("Text folder cleaned.")

# ================================
# Task 2: Convert HTML to Text
# ================================

def convert_html_to_text():
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

                # Clean up the text (removes leading and trailing whitespace)
                cleaned_text = '\n'.join(line.strip() for line in text.splitlines())

                with open(output_file_path, 'w', encoding='utf-8') as file:
                    file.write(cleaned_text)

                print(f'Converted {input_file_path} to plain text at {output_file_path}.')

# ================================
# Task 2: Remove Blank Lines from Text Files
# ================================

def remove_all_blank_lines(file_path):
    """Remove blank lines from a text file and save output in-place."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # Remove all blank lines, handling files in-place
    cleaned_content = [line for line in content if line.strip()]

    # Write cleaned content back to the same file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(cleaned_content)

def apply_blank_removal_in_place(source_folder):
    """Processes text files by removing blank lines and modifying in-place."""
    for root, dirs, files in os.walk(source_folder):
        for filename in files:
            if filename.endswith('.txt'):
                source_path = os.path.join(root, filename)
                remove_all_blank_lines(source_path)
                print(f'Removed blank lines from {source_path}')

# ================================
# Task Definitions
# ================================

# Task: Clean the Text Folder
clean_txt_folder_task = PythonOperator(
    task_id='clean_txt_folder',
    python_callable=clean_txt_folder,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# Task: Convert HTML to Text
convert_html_to_text_task = PythonOperator(
    task_id='convert_html_to_text',
    python_callable=convert_html_to_text,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# Task: Remove Blank Lines In-place
remove_blank_lines_task = PythonOperator(
    task_id='remove_blank_lines',
    python_callable=lambda: apply_blank_removal_in_place(
        source_folder=os.path.join(BASE_PATH, TXT_DIR)
    ),
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

#Trigger the S3 upload DAG after transformations finish
trigger_s3_upload = TriggerDagRunOperator(
    task_id='trigger_upload_to_s3',
    trigger_dag_id='upload_data_to_s3_dag',  # Name of the DAG to trigger
    wait_for_completion=False,               # Do not wait for the upload DAG to complete
    trigger_rule='all_success',              # Trigger S3 upload only if the scraper succeeds completely
    dag=dag
)

# ================================
# Set Up Task Dependencies
# ================================

# Clean Text Folder -> Convert HTML to Text -> Remove Blank Lines -> Trigger S3 Upload
clean_txt_folder_task >> convert_html_to_text_task >> remove_blank_lines_task >> trigger_s3_upload
