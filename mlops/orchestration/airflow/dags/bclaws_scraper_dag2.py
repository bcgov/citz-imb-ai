from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import requests
import shutil
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import ssl
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://www.bclaws.gov.bc.ca/civix/content/complete/statreg/"
BASE_PATH = "/opt/airflow/"
BCLAWS_DIR = "data/bclaws"
XML_DIR = "data/bclaws/xml"

# Retry configuration: retry up to 3 times, with an exponential backoff.
retry_config = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(min=1, max=10),
}

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
    'bclaws_scraper_dag2',
    default_args=default_args,
    description='A DAG to scrape and download laws from BC Laws',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['bclaws', 'scraping'],
)


# Helper functions for modularization
def construct_download_url(index_id, doc_id):
    return f"https://www.bclaws.gov.bc.ca/civix/document/id/complete/{index_id}/{doc_id}/xml"

def get_sanitized_title(title):
    return ''.join(c if c.isalnum() or c.isspace() else '_' for c in title).replace(' ', '_')

def create_folder_if_not_exists(path):
    os.makedirs(path, exist_ok=True)

# === Fetch content and download functions converted to synchronous code ===

@retry(**retry_config)  # Retry on failure with tenacity
def fetch_content(url):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        content = response.content
        return BeautifulSoup(content, 'xml')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None


@retry(**retry_config)  # Retry on failure with tenacity
def download_xml(url, filename):
    try:
        response = requests.get(url, stream=True, verify=False)
        response.raise_for_status()  # Raise an exception for 4xx/5xx HTTP codes

        create_folder_if_not_exists(os.path.dirname(filename))

        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # Filter out keep-alive new chunks
                    file.write(chunk)
        print(f"Successfully downloaded: {filename}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")


# === Processing directory and handling files ===

def process_directory(url, depth=0, parent_path=""):
    soup = fetch_content(url)
    if not soup:
        return

    for element in soup.find_all(['dir', 'document']):
        doc_id = element.find('CIVIX_DOCUMENT_ID')
        if not doc_id:
            continue

        doc_id = doc_id.text
        index_id = element.find('CIVIX_INDEX_ID').text
        is_visible = element.find('CIVIX_DOCUMENT_VISIBLE')
        is_visible = is_visible.text if is_visible else "true"

        if element.name == 'dir':
            next_url = f"{BASE_URL}{parent_path}/{doc_id}"
            process_directory(next_url, depth + 1, f"{parent_path}/{doc_id}")
        elif element.name == 'document':
            if is_visible == "false":
                doc_id += "_multi"

            title = element.find('CIVIX_DOCUMENT_TITLE').text
            sanitized_title = get_sanitized_title(title)
            download_url = construct_download_url(index_id, doc_id)
            filename = os.path.join(BASE_PATH, BCLAWS_DIR, f"{sanitized_title}.xml")

            download_xml(download_url, filename)


def run_scraper():
    """Main function to scrape the given URL and download XML files."""
    create_folder_if_not_exists(os.path.join(BASE_PATH, BCLAWS_DIR))
    process_directory(BASE_URL)
    print("Download completed.")


# === Move files to respective folders ===

def move_files_to_folders():
    source_folder = os.path.join(BASE_PATH, BCLAWS_DIR)
    destination_folder = os.path.join(BASE_PATH, XML_DIR)
    
    create_folder_if_not_exists(destination_folder)

    for file_name in os.listdir(source_folder):
        file_path = os.path.join(source_folder, file_name)
        if os.path.isfile(file_path) and file_path.endswith('.xml'):
            # Check for "REPEALED BY B.C." in the file content
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                if any(elem.text and "REPEALED BY B.C." in elem.text for elem in root.iter()):
                    target_folder = os.path.join(destination_folder, "Repealed")
                    create_folder_if_not_exists(target_folder)
                    shutil.move(file_path, os.path.join(target_folder, file_name))
                    continue
            except ET.ParseError:
                print(f"Error parsing {file_name}. Skipping...")
                continue

            # Determine the appropriate folder based on file name patterns
            target_folder = get_target_folder(file_name)

            create_folder_if_not_exists(target_folder)
            shutil.move(file_path, os.path.join(target_folder, file_name))
    
    print("File sorting and moving completed.")


def get_target_folder(file_name):
    """Determine the appropriate folder based on file name patterns."""
    if "Edition_TLC" in file_name:
        return os.path.join(BASE_PATH, XML_DIR, "Editions")
    elif "Table_of_Contents_" in file_name:
        return os.path.join(BASE_PATH, XML_DIR, "Table of Contents")
    elif file_name.startswith("Historical_Table_"):
        return os.path.join(BASE_PATH, XML_DIR, "Historical Tables")
    elif file_name.startswith("Appendices_") or file_name.startswith("Appendix_"):
        return os.path.join(BASE_PATH, XML_DIR, "Appendix")
    elif file_name.startswith("Chapter_"):
        return os.path.join(BASE_PATH, XML_DIR, "Chapters")
    elif file_name.startswith("Part"):
        return os.path.join(BASE_PATH, XML_DIR, "Parts")
    elif file_name.startswith("Point_in_Time_"):
        return os.path.join(BASE_PATH, XML_DIR, "Point in Times")
    elif "Regulation" in file_name:
        return os.path.join(BASE_PATH, XML_DIR, "Regulations")
    elif "Schedule" in file_name:
        return os.path.join(BASE_PATH, XML_DIR, "Schedules")
    elif "Sections_" in file_name:
        return os.path.join(BASE_PATH, XML_DIR, "Sections")
    elif "Rule" in file_name:
        return os.path.join(BASE_PATH, XML_DIR, "Rules")
    elif file_name.endswith("_Act.xml"):
        return os.path.join(BASE_PATH, XML_DIR, "Acts")
    else:
        return os.path.join(BASE_PATH, XML_DIR, "Others")  # Catch-all for uncategorized files


# === DAG task creation ===

scrape_task = PythonOperator(
    task_id='scrape_bclaws',
    python_callable=run_scraper,
    dag=dag,
)

sort_files_task = PythonOperator(
    task_id='sort_files',
    python_callable=move_files_to_folders,
    dag=dag,
)

scrape_task >> sort_files_task
