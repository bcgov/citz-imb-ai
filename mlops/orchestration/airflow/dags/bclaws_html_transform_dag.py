import os
import re
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta

# ================================
# Constants and Configuration Setup
# ================================

BASE_PATH = "/opt/airflow/"
HTML_DIR = "data/bclaws/html"

# Retry configuration for task failures
RETRY_CONFIG = {
    "retries": 3,  # Max retry attempts
    "retry_delay": timedelta(minutes=5),  # Delay between retries
}

# Default arguments for DAG tasks
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
    'bclaws_html_transform_dag',
    default_args=default_args,
    description='A DAG to transform downloaded BC Laws HTML data',
    schedule_interval=None,  # This will be triggered externally
    catchup=False,
    tags=['bclaws', 'transformation'],
)

# ================================
# Transformation Functions
# ================================

def handle_unicode_errors():
    """Replace invalid Unicode characters in HTML files."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                # Process each HTML file
                file_path = os.path.join(root, filename)
                try:
                    # Read with 'replace' to handle Unicode errors
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                        content = file.read()

                    # Write back the cleaned content
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)

                    print(f'Repaired Unicode in {filename} in {root}')
                
                except Exception as e:
                    print(f"Failed to handle Unicode for {file_path}: {e}")


def prettify_html_files():
    """Improve HTML formatting for all files."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                # Process each HTML file
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Use BeautifulSoup to prettify HTML
                formatter = HTMLFormatter(indent=3)
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.prettify(formatter=formatter)

                # Write back the prettified content
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f'Prettified {filename} in {root}')


def remove_unwanted_tags():
    """Clean up HTML by removing unnecessary tags and attributes."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                # Process each HTML file
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Remove various unwanted elements
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

                # Write back the cleaned content
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f'Tags removed from {filename} in {root}')


def final_prettify():
    """Perform final HTML prettification."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)
    
    for root, dirs, files in os.walk(downloads_folder):
        for filename in files:
            if filename.endswith(".html"):
                # Process each HTML file
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Use BeautifulSoup to prettify HTML
                formatter = HTMLFormatter(indent=3)
                soup = BeautifulSoup(content, 'html.parser')
                content = soup.prettify(formatter=formatter)

                # Write back the prettified content
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                print(f'Final prettification done for {filename} in {root}')


def fix_html_tasks():
    """Fix HTML structure issues in all files."""
    downloads_folder = os.path.join(BASE_PATH, HTML_DIR)

    for root, _, files in os.walk(downloads_folder):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                fix_html(file_path)


def fix_html(file_path):
    """Fix nested <p> tags and block-level elements inside <p> tags."""
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Remove nested <p> tags
    html_content = re.sub(r'<p[^>]*>\s*<p', '<p', html_content)
    html_content = re.sub(r'</p>\s*</p>', '</p>', html_content)

    soup = BeautifulSoup(html_content, 'html.parser')

    # Fix <p> tags containing block-level elements
    for p in soup.find_all('p'):
        if p.find(['div', 'p']):
            new_tag = soup.new_tag('div')
            new_tag.extend(p.contents)
            p.replace_with(new_tag)

    # Write back the fixed content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))

    print(f"Fixed: {file_path}")


# ================================
# Task Definitions
# ================================

# Task to handle Unicode errors
handle_unicode_errors_task = PythonOperator(
    task_id='handle_unicode_errors',
    python_callable=handle_unicode_errors,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# Task to fix HTML structure
fix_html_task = PythonOperator(
    task_id='fix_html',
    python_callable=fix_html_tasks,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# Task for initial HTML prettification
prettify_html_task = PythonOperator(
    task_id='prettify_html',
    python_callable=prettify_html_files,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# Task to remove unwanted HTML elements
remove_unwanted_tags_task = PythonOperator(
    task_id='remove_unwanted_tags',
    python_callable=remove_unwanted_tags,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# Task for final HTML prettification
final_prettify_task = PythonOperator(
    task_id='final_prettify',
    python_callable=final_prettify,
    dag=dag,
    retries=RETRY_CONFIG["retries"],
    retry_delay=RETRY_CONFIG["retry_delay"],
)

# Task to trigger the text transformation DAG
trigger_txt_transform_task = TriggerDagRunOperator(
    task_id='trigger_bclaws_txt_transform_dag',
    trigger_dag_id='bclaws_txt_transform_dag',
    wait_for_completion=False,  # Don't wait for text DAG to finish
    trigger_rule='all_success',
    dag=dag,
)

# ================================
# Set Up Task Dependencies
# ================================

# Define the order of task execution
handle_unicode_errors_task >> fix_html_task >> prettify_html_task >> remove_unwanted_tags_task >> final_prettify_task >> trigger_txt_transform_task
