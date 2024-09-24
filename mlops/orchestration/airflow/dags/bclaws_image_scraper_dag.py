from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import re
import requests
from lxml import etree

# ================================
# Constants and Configuration Setup
# ================================

# Base URL for images
BASE_URL = 'https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/'

# Directory paths for where images are stored
BASE_PATH = "/opt/airflow/"
XML_DIR = "data/bclaws/xml"  # Folder for XML files
IMAGE_DIR = "data/bclaws/images"  # Folder for downloaded images

# Retry configuration for HTTP requests when downloading images
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),  # Max 3 retry attempts
    "wait": wait_exponential(min=1, max=10),  # Exponential backoff between retries
}

# Supported image extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 9, 11),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'bclaws_image_scraper_dag',
    default_args=default_args,
    description='A DAG to scrape images from XML files and skip low-quality versions',
    schedule_interval=None,  # Run the DAG manually or trigger externally as needed
    catchup=False,
    tags=['bclaws', 'scraping', 'images'],
)

# ================================
# Helper Functions
# ================================

def create_folder_if_not_exists(folder_path):
    """Create folder if it doesn't exist."""
    try:
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created directory: {folder_path}")
    except Exception as e:
        print(f"Failed to create directory {folder_path}. Reason: {e}")

@retry(**RETRY_CONFIG)
def download_image(url, save_path):
    """Download an image and save it locally."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as out_file:
            for chunk in response.iter_content(1024):
                out_file.write(chunk)
        print(f"Downloaded {url} to {save_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return False

def is_low_quality_version(filename, all_filenames):
    """Identify and skip low-quality images."""
    low_quality_patterns = [
        r"_sm_",  # pattern like "07043_sm_T_1_Watershed_Huu_RGB"
        r"_\.",   # trailing underscore before the extension, e.g., "99002_appendix-a-1_.jpg"
    ]

    for pattern in low_quality_patterns:
        if re.search(pattern, filename):
            base_filename = re.sub(pattern, "", filename)
            # In case of trailing underscore before extension, remove the last underscore for comparison
            base_filename = re.sub(r"_\.", ".", base_filename)
            if base_filename in all_filenames:
                print(f"Low-quality version detected: {filename}, skipping in favor of {base_filename}")
                return True
    return False

def scrape_images_from_xml(xml_file_path):
    """Scrape images from XML and skip low-quality versions."""
    xml_relative_path = os.path.relpath(xml_file_path, start=os.path.join(BASE_PATH, XML_DIR))
    image_save_folder = os.path.join(BASE_PATH, IMAGE_DIR, os.path.dirname(xml_relative_path))

    create_folder_if_not_exists(image_save_folder)

    all_image_filenames = []

    with open(xml_file_path, 'r', encoding='utf-8') as xml_file:
        tree = etree.parse(xml_file)
        root = tree.getroot()

        # Collect all filenames
        for element in root.iter():
            href = element.get('href')
            if href and any(href.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                if "/statreg/" in href:
                    image_name = href.split('/statreg/')[-1]
                    all_image_filenames.append(image_name)

        # Download images while skipping low-quality versions
        for element in root.iter():
            href = element.get('href')
            if href and any(href.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                if "/statreg/" in href:
                    image_name = href.split('/statreg/')[-1]

                    if is_low_quality_version(image_name, all_image_filenames):
                        continue

                    image_url = BASE_URL + image_name
                    save_path = os.path.join(image_save_folder, image_name)
                    download_image(image_url, save_path)

def list_xml_files(xml_folder):
    """List all XML files in a directory."""
    xml_files = []
    for root, _, files in os.walk(xml_folder):
        for file in files:
            if file.endswith(".xml"):
                xml_files.append(os.path.join(root, file))
    return xml_files

def run_image_scraper():
    """Main function to run image scraping for all XML files."""
    xml_folder = os.path.join(BASE_PATH, XML_DIR)
    xml_files = list_xml_files(xml_folder)
    for xml_file in xml_files:
        scrape_images_from_xml(xml_file)
    print("Image scraping completed.")

# ===============================
# Task Definitions and DAG Setup
# ===============================

# Task 1: Image Scraping
scrape_images_task = PythonOperator(
    task_id='scrape_bclaws_images',
    python_callable=run_image_scraper,
    dag=dag,
)

