from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import ssl
import shutil
import xml.etree.ElementTree as ET

BASE_URL = "https://www.bclaws.gov.bc.ca/civix/content/complete/statreg/"
BASE_PATH = "/opt/airflow/"
BCLAWS_DIR = "data/bclaws"
XML_DIR = "data/bclaws/xml"

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
    tags=['bclaws', 'scraping'],
)

async def fetch_content(url, session):
    try:
        async with session.get(url, ssl=False) as response:
            content = await response.text()
            return BeautifulSoup(content, 'xml')
    except Exception as error:
        print(f"Error fetching URL {url}: {str(error)}")
        return None

async def download_xml(url, filename, session):
    try:
        async with session.get(url, ssl=False) as response:
            if response.status != 200:
                print(f"Failed to download {url}: HTTP {response.status}")
                return
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            async with aiofiles.open(filename, 'wb') as writer:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await writer.write(chunk)
        print(f"Successfully downloaded: {filename}")
    except Exception as error:
        print(f"Error downloading file {url}: {str(error)}")

async def process_directory(url, session, depth=0, parent_path=""):
    soup = await fetch_content(url, session)
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
            await process_directory(next_url, session, depth + 1, f"{parent_path}/{doc_id}")
        elif element.name == 'document':
            if is_visible == "false":
                doc_id += "_multi"
            
            title = element.find('CIVIX_DOCUMENT_TITLE').text
            sanitized_title = ''.join(c if c.isalnum() or c.isspace() else '_' for c in title).replace(' ', '_')
            
            download_url = f"https://www.bclaws.gov.bc.ca/civix/document/id/complete/{index_id}/{doc_id}/xml"
            filename = os.path.join(BASE_PATH, BCLAWS_DIR, f"{sanitized_title}.xml")
            
            await download_xml(download_url, filename, session)

async def main():
    os.makedirs(os.path.join(BASE_PATH, BCLAWS_DIR), exist_ok=True)
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        await process_directory(BASE_URL, session)
    print("Download completed.")

def run_scraper():
    asyncio.run(main())

def move_files_to_folders():
    source_folder = os.path.join(BASE_PATH, BCLAWS_DIR)
    destination_folder = os.path.join(BASE_PATH, XML_DIR)
    
    # Ensure the destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

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
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(file_path, os.path.join(target_folder, file_name))
                    continue
            except ET.ParseError:
                print(f"Error parsing {file_name}. Skipping...")
                continue

            # Determine the appropriate folder based on file name patterns
            if "Edition_TLC" in file_name:
                target_folder = os.path.join(destination_folder, "Editions")
            elif file_name.startswith("Historical_Table_"):
                target_folder = os.path.join(destination_folder, "Historical Tables")
            elif file_name.startswith("Appendices_") or file_name.startswith("Appendix_"):
                target_folder = os.path.join(destination_folder, "Appendix")
            elif file_name.startswith("Chapter_"):
                target_folder = os.path.join(destination_folder, "Chapters")
            elif file_name.startswith("Part"):
                target_folder = os.path.join(destination_folder, "Parts")
            elif file_name.startswith("Point_in_Time_"):
                target_folder = os.path.join(destination_folder, "Point in Times")
            elif "Regulation" in file_name:
                target_folder = os.path.join(destination_folder, "Regulations")
            elif "Schedule" in file_name:
                target_folder = os.path.join(destination_folder, "Schedules")
            elif "Sections_" in file_name:
                target_folder = os.path.join(destination_folder, "Sections")
            elif "Rule" in file_name:
                target_folder = os.path.join(destination_folder, "Rules")
            elif file_name.endswith("_Act.xml"):
                target_folder = os.path.join(destination_folder, "Acts")
            else:
                # Move remaining files to the "Others" folder
                target_folder = os.path.join(destination_folder, "Others")

            # Create the target folder if it doesn't exist and move the file
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            shutil.move(file_path, os.path.join(target_folder, file_name))
    
    print("File sorting and moving completed.")

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
