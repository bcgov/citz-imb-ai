from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable  # For persisting and retrieving the last modified time
from datetime import datetime, timedelta
import os
import requests
import shutil
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import ssl
from tenacity import retry, stop_after_attempt, wait_exponential

# Constants
BASE_URL = "https://www.bclaws.gov.bc.ca/civix/content/complete/statreg/"
CHECK_CHANGES_URL = "https://www.bclaws.gov.bc.ca/civix/index/complete/statreg/document.xml"
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
    'bclaws_scraper_dag',
    default_args=default_args,
    description='A DAG to scrape and download laws from BC Laws',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['bclaws', 'scraping'],
)

# ==========================================
# 1. Function to Parse and Compare Last Modified Time
# ==========================================
def parse_last_modified():
    """
    Fetch the latest 'lastModified' value from the API and compare it
    to the stored value in Airflow Variables. If the last modified time
    has changed, trigger scraping.
    """
    try:
        response = requests.get(CHECK_CHANGES_URL, verify=False)
        response.raise_for_status()

        # Parse the XML response
        soup = BeautifulSoup(response.content, 'xml')
        
        # Find the top-level ix:dir element (get the first one as an example) and extract its 'lastModified' attribute
        latest_last_modified = soup.find('ix:dir')['lastModified']

        # Convert the string to a datetime object
        latest_modified_time = datetime.strptime(latest_last_modified, "%m/%d/%Y %I:%M:%S %p")
        
        # Retrieve previously stored 'last_modified' value from Airflow Variables (if empty, set a default older date)
        previous_modified_time = Variable.get("bclaws_last_modified", default_var="01/01/2000 12:00:00 AM")
        previous_modified_time = datetime.strptime(previous_modified_time, "%m/%d/%Y %I:%M:%S %p")  # Convert string to datetime

        # If the latest modified time is newer, update the Airflow Variable and trigger further tasks
        if latest_modified_time > previous_modified_time:
            # Update the variable to the new latest modified time
            Variable.set("bclaws_last_modified", latest_last_modified)
            return 'scrape_bclaws'
        else:
            # If no update has occurred
            return 'no_changes'

    except requests.exceptions.RequestException as e:
        print(f"Error during API call or XML parsing: {e}")
        return 'no_changes'  # On error, we assume no changes

# ==========================================
# 2. Define the existing scraping and sorting tasks (same as before)
# ==========================================
def construct_download_url(index_id, doc_id):
    return f"https://www.bclaws.gov.bc.ca/civix/document/id/complete/{index_id}/{doc_id}/xml"

def get_sanitized_title(title):
    return ''.join(c if c.isalnum() or c.isspace() else '_' for c in title).replace(' ', '_')

def create_folder_if_not_exists(path):
    os.makedirs(path, exist_ok=True)

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

def move_files_to_folders():
    source_folder = os.path.join(BASE_PATH, BCLAWS_DIR)
    destination_folder = os.path.join(BASE_PATH, XML_DIR)
    
    create_folder_if_not_exists(destination_folder)

    # Initialize a set to keep track of files that are sorted (moved to other folders)
    sorted_files = set()

    for file_name in os.listdir(source_folder):
        file_path = os.path.join(source_folder, file_name)
        if os.path.isfile(file_path) and file_path.endswith('.xml'):
            # Check for "Table_of_Contents_" and delete the file if found
            if "Table_of_Contents_" in file_name:
                os.remove(file_path)
                print(f'Deleted {file_name}')
                continue
            
            # Check for "REPEALED BY B.C." in the file content
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                if any(elem.text and "REPEALED BY B.C." in elem.text for elem in root.iter()):
                    target_folder = os.path.join(destination_folder, "Repealed")
                    create_folder_if_not_exists(target_folder)
                    shutil.move(file_path, os.path.join(target_folder, file_name))
                    print(f"Moved {file_name} to Repealed folder.")
                    sorted_files.add(file_name)  # Track as processed
                    continue
            except ET.ParseError:
                print(f"Error parsing {file_name}. Skipping...")
                continue

            # Determine the appropriate folder based on file name patterns
            target_folder = get_target_folder(file_name)

            create_folder_if_not_exists(target_folder)
            shutil.move(file_path, os.path.join(target_folder, file_name))
            print(f"Moved {file_name} to {os.path.basename(target_folder)} folder.")
            sorted_files.add(file_name)  # Track as processed
    
    # Clean up remaining files that have not been processed
    for file_name in os.listdir(source_folder):
        if file_name.endswith(".xml") and file_name not in sorted_files:
            file_path = os.path.join(source_folder, file_name)
            os.remove(file_path)
            print(f"Deleted unsorted file: {file_name}")
    
    # All files processed
    print("File sorting and cleanup completed.")

def get_target_folder(file_name):
    """Determine the appropriate folder based on file name patterns."""
    if "Edition_TLC" in file_name:
        return os.path.join(BASE_PATH, XML_DIR, "Editions")
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

# ==========================================
# 3. Define the Airflow DAG and Task Creation
# ==========================================

# Task 1: Branching task that checks if changes exist
check_changes_task = BranchPythonOperator(
    task_id='check_for_changes',
    python_callable=parse_last_modified,
    dag=dag,
)

# Task 2: Task to run the scraper and download files (only if changes detected)
scrape_task = PythonOperator(
    task_id='scrape_bclaws',
    python_callable=run_scraper,
    dag=dag,
)

# Task 3: Task to handle file sorting after download
sort_files_task = PythonOperator(
    task_id='sort_files',
    python_callable=move_files_to_folders,
    dag=dag,
)

# Dummy Task: No changes (Gracefully end the DAG without scraping)
no_changes_task = DummyOperator(
    task_id='no_changes',
    dag=dag,
)

# ==========================================
# 4. Set Up Task Dependencies
# ==========================================
check_changes_task >> [scrape_task, no_changes_task]  # If changes, scrape. If no changes, end gracefully.
scrape_task >> sort_files_task  # Sort files only after scraping is completed
