from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import ssl

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

scrape_task = PythonOperator(
    task_id='scrape_bclaws',
    python_callable=run_scraper,
    dag=dag,
)

scrape_task
