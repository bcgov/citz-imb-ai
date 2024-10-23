from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import os
import re
import requests
from lxml import etree
from typing import Dict, List, Set
import time
from collections import defaultdict

# ================================
# Constants and Configuration Setup
# ================================

BASE_URL = 'https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/'
BASE_PATH = "/opt/airflow/"
XML_DIR = "data/bclaws/xml"
IMAGE_DIR = "data/bclaws/images"

# Rate limiting configuration
RATE_LIMIT_DELAY = 1  # Seconds between API calls
MAX_CONCURRENT_DOWNLOADS = 5  # Maximum concurrent downloads

# Retry configuration
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(min=1, max=10),
}

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']

# Prefixes of images to remove
REMOVE_PREFIXES = {
    'bcsigb', 'bracket', 'checkbox', 'parenthesis',
    'parleft', 'parright', 'arrow_', 'brace'
}

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 9, 24),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'bclaws_image_scraper_dag',
    default_args=default_args,
    description='A DAG to scrape images from XML files with improved organization',
    schedule_interval=None,
    catchup=False,
    tags=['bclaws', 'scraping', 'images'],
)

# ================================
# Helper Classes
# ================================

class ImageCollector:
    def __init__(self):
        self.image_map: Dict[str, Set[str]] = defaultdict(set)
        
    def add_image(self, xml_path: str, image_url: str):
        """Add image URL to the collection, organized by XML source"""
        self.image_map[xml_path].add(image_url)
    
    def get_all_images(self) -> Dict[str, Set[str]]:
        return self.image_map

class ImageFilter:
    @staticmethod
    def is_low_quality(filename: str, all_urls: Set[str]) -> bool:
        """Determine if an image is low quality based on defined rules"""
        if any(filename.lower().startswith(prefix) for prefix in REMOVE_PREFIXES):
            return True
            
        if "_sm_" in filename or "_sm-" in filename:
            high_quality = filename.replace("_sm_", "_lg_").replace("_sm-", "_lg-")
            return any(high_quality in url for url in all_urls)
            
        if re.search(r"_\.[^.]+$", filename):
            base_name = re.sub(r"_(\.[^.]+)$", r"\1", filename)
            return any(base_name in url for url in all_urls)
            
        return False

# ================================
# Core Functions
# ================================

def collect_image_urls() -> ImageCollector:
    """Traverse all XML files and collect image URLs"""
    collector = ImageCollector()
    xml_folder = os.path.join(BASE_PATH, XML_DIR)
    
    for root, _, files in os.walk(xml_folder):
        for file in files:
            if file.endswith('.xml'):
                xml_path = os.path.join(root, file)
                try:
                    tree = etree.parse(xml_path)
                    for element in tree.iter():
                        href = element.get('href')
                        if href and any(href.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                            if "/statreg/" in href:
                                image_name = href.split('/statreg/')[-1]
                                image_url = BASE_URL + image_name
                                collector.add_image(xml_path, image_url)
                except Exception as e:
                    print(f"Error processing {xml_path}: {e}")
    
    return collector

def filter_images(collector: ImageCollector) -> Dict[str, List[str]]:
    """Filter out low-quality images from the collection"""
    filtered_images = {}
    image_filter = ImageFilter()
    
    for xml_path, urls in collector.get_all_images().items():
        all_urls = set(urls)
        filtered_urls = [
            url for url in urls
            if not image_filter.is_low_quality(url.split('/')[-1], all_urls)
        ]
        filtered_images[xml_path] = filtered_urls
    
    return filtered_images

@retry(**RETRY_CONFIG)
def download_image(url: str, save_path: str):
    """Download an image with rate limiting"""
    try:
        time.sleep(RATE_LIMIT_DELAY)  # Rate limiting
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as out_file:
            for chunk in response.iter_content(1024):
                out_file.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_filtered_images(filtered_images: Dict[str, List[str]]):
    """Download filtered images maintaining folder structure"""
    for xml_path, urls in filtered_images.items():
        # Create folder structure based on XML path
        rel_path = os.path.relpath(xml_path, start=os.path.join(BASE_PATH, XML_DIR))
        image_folder = os.path.join(BASE_PATH, IMAGE_DIR, 
                                os.path.splitext(rel_path)[0])
        
        os.makedirs(image_folder, exist_ok=True)
        
        # Download images with rate limiting
        for url in urls:
            filename = url.split('/')[-1]
            save_path = os.path.join(image_folder, filename)
            download_image(url, save_path)

def cleanup_empty_folders():
    """Remove empty folders after processing"""
    image_base_path = os.path.join(BASE_PATH, IMAGE_DIR)
    for root, dirs, files in os.walk(image_base_path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):
                os.rmdir(dir_path)

def process_images():
    """Main process to collect, filter, and download images"""
    # Step 1: Collect all image URLs
    collector = collect_image_urls()
    print(f"Collected images from {len(collector.get_all_images())} XML files")
    
    # Step 2: Filter images
    filtered_images = filter_images(collector)
    print("Filtered out low-quality images")
    
    # Step 3: Download filtered images
    download_filtered_images(filtered_images)
    print("Downloaded all filtered images")

# ================================
# DAG Tasks
# ================================

process_images_task = PythonOperator(
    task_id='process_images',
    python_callable=process_images,
    dag=dag,
)

cleanup_task = PythonOperator(
    task_id='cleanup_empty_folders',
    python_callable=cleanup_empty_folders,
    dag=dag,
)

trigger_s3_upload = TriggerDagRunOperator(
    task_id='trigger_upload_to_s3',
    trigger_dag_id='upload_data_to_s3_dag',  # Name of the DAG to trigger
    wait_for_completion=False,               # Do not wait for the upload DAG to complete
    trigger_rule='all_success',              # Trigger S3 upload only if the scraper succeeds completely
    dag=dag
)

# Set task dependencies
process_images_task >> cleanup_task >> trigger_s3_upload
