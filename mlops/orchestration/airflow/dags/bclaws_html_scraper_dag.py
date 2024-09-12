from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from datetime import datetime, timedelta
import os
import requests
import shutil
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

# ================================
# Constants and Configuration Setup
# ================================

# URL constants for scraping BC laws
BASE_URL = "https://www.bclaws.gov.bc.ca/civix/content/complete/statreg/"

# Directory paths for where files are stored
BASE_PATH = "/opt/airflow/"
HTML_DIR = "data/bclaws/html"  # Folder for HTML files

# Retry behavior configuration when making HTTP requests
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),  # Retry up to 3 times
    "wait": wait_exponential(min=1, max=10),  # Exponential backoff
}

# Default argument configuration for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 9, 11),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'bclaws_html_scraper_dag',
    default_args=default_args,
    description='A DAG to scrape and download HTML laws from BC Laws',
    schedule_interval=None,  # This will be triggered by an external DAG
    catchup=False,
    tags=['bclaws', 'scraping'],
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
# Task 1: Cleaning HTML Folder
# ===============================

def clean_html_folder():
    """Clean the HTML directory before starting the scraper and ensure the folder exists."""
    folder = os.path.join(BASE_PATH, HTML_DIR)

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
    
    print("HTML folder cleaned.")

# ================================
# Task 2: Scraping Logic (Fetch Data)
# ================================

def construct_download_url(index_id, doc_id):
    """Generate the URL for downloading a specific document (HTML in this case)."""
    return f"https://www.bclaws.gov.bc.ca/civix/document/id/complete/{index_id}/{doc_id}"

def get_sanitized_title(title):
    """Sanitize document titles to be suitable for filenames."""
    return ''.join(c if c.isalnum() or c.isspace() else '_' for c in title).replace(' ', '_')

@retry(**RETRY_CONFIG)
def fetch_content(url):
    """Fetch content by making a request, and return the parsed HTML."""
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'xml')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

@retry(**RETRY_CONFIG)
def download_html(url, filename):
    """Download an HTML file from the given URL and save it to the specified location."""
    try:
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()
        create_folder_if_not_exists(os.path.dirname(filename))

        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"Successfully downloaded: {filename}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

def process_directory(url, depth=0, parent_path=""):
    """Recursively process the directory to download relevant HTML files."""
    soup = fetch_content(url)
    if not soup:
        return

    for element in soup.find_all(['dir', 'document']):
        doc_id = element.find('CIVIX_DOCUMENT_ID')
        if not doc_id:
            continue

        doc_id = doc_id.text
        index_id = element.find('CIVIX_INDEX_ID').text
        is_visible = element.find('CIVIX_DOCUMENT_VISIBLE').text if element.find('CIVIX_DOCUMENT_VISIBLE') else "true"

        if element.name == 'dir':
            next_url = f"{BASE_URL}{parent_path}/{doc_id}"
            process_directory(next_url, depth + 1, f"{parent_path}/{doc_id}")
        elif element.name == 'document':
            if is_visible == "false":
                doc_id += "_multi"
            title = element.find('CIVIX_DOCUMENT_TITLE').text
            sanitized_title = get_sanitized_title(title)
            download_url = construct_download_url(index_id, doc_id)
            filename = os.path.join(BASE_PATH, HTML_DIR, f"{sanitized_title}.html")
            download_html(download_url, filename)

def run_scraper():
    """Main function to run the entire scraping process for HTML files."""
    create_folder_if_not_exists(os.path.join(BASE_PATH, HTML_DIR))
    process_directory(BASE_URL)
    print("Download completed.")

# ===============================
# Task 3: Sorting Downloaded Files
# ===============================

def move_files_to_folders():
    """Sort files into the appropriate subfolders after downloading."""
    folder = os.path.join(BASE_PATH, HTML_DIR)
    sorted_files = set()

    for file_name in os.listdir(folder):
        file_path = os.path.join(folder, file_name)

        if os.path.isfile(file_path) and file_path.endswith('.html'):
            ### General Sorting (Handle other files based on the filename pattern) ###
            target_folder = get_target_folder(file_name)
            create_folder_if_not_exists(target_folder)
            shutil.move(file_path, os.path.join(target_folder, file_name))
            print(f"Moved {file_name} to {os.path.basename(target_folder)} folder.")
            sorted_files.add(file_name)
    
    print("File sorting completed.")

def get_target_folder(file_name):
    folder = os.path.join(BASE_PATH, HTML_DIR)  # Target folder is within HTML_DIR
    if "Edition_TLC" in file_name:
        return os.path.join(folder, "Editions")
    elif file_name.startswith("Historical_Table_"):
        return os.path.join(folder, "Historical_Tables")
    elif file_name.startswith("Appendices_") or file_name.startswith("Appendix_"):
        return os.path.join(folder, "Appendix")
    elif file_name.startswith("Chapter_"):
        return os.path.join(folder, "Chapters")
    elif file_name.startswith("Part"):
        return os.path.join(folder, "Parts")
    elif "Regulation" in file_name:
        return os.path.join(folder, "Regulations")
    elif "Schedule" in file_name:
        return os.path.join(folder, "Schedules")
    elif "Sections_" in file_name:
        return os.path.join(folder, "Sections")
    elif "Rule" in file_name:
        return os.path.join(folder, "Rules")
    elif file_name.endswith("_Act.html"):
        return os.path.join(folder, "Acts")
    else:
        return os.path.join(folder, "Others")

# ===============================
# Define the DAG Workflow and Task Dependencies
# ===============================

# Step 1: Clean the HTML directory
clean_html_folder_task = PythonOperator(
    task_id='clean_html_folder',
    python_callable=clean_html_folder,  # Clean directory before scraping
    dag=dag,
)

# Step 2: Run the scraping process for HTML files
scrape_task = PythonOperator(
    task_id='scrape_bclaws',
    python_callable=run_scraper,  # Download files
    dag=dag,
)

# Step 3: After scraping, sort the downloaded files
sort_files_task = PythonOperator(
    task_id='sort_files',
    python_callable=move_files_to_folders,  # Organize sorted files
    dag=dag,
)

# Step 4: Trigger the HTML Scraper DAG after XML Scraper finishes
trigger_html_transform = TriggerDagRunOperator(
    task_id='trigger_html_transform',
    trigger_dag_id='bclaws_html_transform_dag',  # Name of the DAG to trigger
    wait_for_completion=False,               # Do not wait for the upload DAG to complete
    trigger_rule='all_success',              # Trigger html scraper only if the xml scraper succeeds completely
    dag=dag
)

# =======================
# Set Up Task Dependencies
# =======================

# Clean before scraping, then sort the files
clean_html_folder_task >> scrape_task  # Clean before scraping
scrape_task >> sort_files_task    # Sort files after scraping
sort_files_task >> trigger_html_transform  # Trigger data transform after sorting is complete
