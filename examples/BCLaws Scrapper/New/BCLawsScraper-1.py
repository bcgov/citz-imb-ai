import os
import time
import requests
import xml.etree.ElementTree as ET
import re
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bclaws_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Constants
BASE_CONTENT_URL = "https://www.bclaws.gov.bc.ca/civix/content/consol43/consol43/"
BASE_DOCUMENT_URL = "https://www.bclaws.gov.bc.ca/civix/document/id/consol43/consol43/"
ROOT_DIR = "Consol43"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RATE_LIMIT_DELAY = 0.5  # seconds

# Ensure the root directory exists
os.makedirs(ROOT_DIR, exist_ok=True)

# Track processed documents to avoid duplicates
processed_doc_ids = set()

def sanitize_filename(name):
    """Sanitize a string to be used as a filename by removing invalid characters."""
    if not name:
        return "untitled"
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    # Limit length to avoid filesystem issues
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + "..."
    return sanitized

def get_xml_from_url(url):
    """Fetch XML from a URL with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return ET.fromstring(response.content)
        except (requests.RequestException, ET.ParseError) as e:
            logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES} failed for {url}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Failed to retrieve {url} after {MAX_RETRIES} attempts")
                raise

def process_directory(content_url, local_dir_path):
    """
    Process a directory in the BC Laws API.
    
    Args:
        content_url: The URL to the content API for this directory
        local_dir_path: The local path where files should be saved
    """
    logger.info(f"Processing directory: {content_url}")
    os.makedirs(local_dir_path, exist_ok=True)
    
    try:
        # Get directory content
        root = get_xml_from_url(content_url)
        
        # Check for documents to download
        found_htm_toc = False
        
        # First pass: Check for HTML TOC documents with order=0
        for doc in root.findall(".//document"):
            doc_type = doc.find("CIVIX_DOCUMENT_TYPE").text if doc.find("CIVIX_DOCUMENT_TYPE") is not None else ""
            doc_ext = doc.find("CIVIX_DOCUMENT_EXT").text if doc.find("CIVIX_DOCUMENT_EXT") is not None else ""
            doc_order = doc.find("CIVIX_DOCUMENT_ORDER").text if doc.find("CIVIX_DOCUMENT_ORDER") is not None else ""
            doc_id = doc.find("CIVIX_DOCUMENT_ID").text if doc.find("CIVIX_DOCUMENT_ID") is not None else ""
            
            if doc_id in processed_doc_ids:
                continue
                
            if doc_type == "document" and doc_order == "0" and doc_ext == "htm":
                # This is an HTML table of contents - download the multi-document version
                doc_title = doc.find("CIVIX_DOCUMENT_TITLE").text
                safe_title = sanitize_filename(doc_title)
                
                logger.info(f"Found HTML TOC document: {doc_title} (ID: {doc_id})")
                download_multi_document(doc_id, safe_title, local_dir_path)
                processed_doc_ids.add(doc_id)
                found_htm_toc = True
                break  # Skip other files in this directory per requirements
        
        # If no HTM table of contents was found, process XML documents
        if not found_htm_toc:
            for doc in root.findall(".//document"):
                doc_type = doc.find("CIVIX_DOCUMENT_TYPE").text if doc.find("CIVIX_DOCUMENT_TYPE") is not None else ""
                doc_ext = doc.find("CIVIX_DOCUMENT_EXT").text if doc.find("CIVIX_DOCUMENT_EXT") is not None else ""
                doc_order = doc.find("CIVIX_DOCUMENT_ORDER").text if doc.find("CIVIX_DOCUMENT_ORDER") is not None else ""
                doc_id = doc.find("CIVIX_DOCUMENT_ID").text if doc.find("CIVIX_DOCUMENT_ID") is not None else ""
                
                if doc_id in processed_doc_ids:
                    continue
                    
                if doc_type == "document" and doc_order == "0" and doc_ext == "xml":
                    # Direct XML document
                    doc_title = doc.find("CIVIX_DOCUMENT_TITLE").text
                    safe_title = sanitize_filename(doc_title)
                    
                    logger.info(f"Found XML document: {doc_title} (ID: {doc_id})")
                    download_document(doc_id, safe_title, local_dir_path)
                    processed_doc_ids.add(doc_id)
        
        # Process subdirectories
        for item in root.findall(".//dir"):
            item_id = item.find("CIVIX_DOCUMENT_ID").text
            item_title = item.find("CIVIX_DOCUMENT_TITLE").text
            safe_title = sanitize_filename(item_title)
            
            # Create subdirectory path and process it
            subdir_path = os.path.join(local_dir_path, safe_title)
            next_url = urljoin(BASE_CONTENT_URL, item_id)
            process_directory(next_url, subdir_path)
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(RATE_LIMIT_DELAY)
    
    except Exception as e:
        logger.error(f"Error processing directory {content_url}: {str(e)}")

def download_document(doc_id, title, local_dir_path):
    """Download a regular XML document."""
    download_url = f"{BASE_DOCUMENT_URL}{doc_id}/xml"
    save_path = os.path.join(local_dir_path, f"{title}.xml")
    
    download_file(download_url, save_path)

def download_multi_document(doc_id, title, local_dir_path):
    """Download a multi-document XML file."""
    download_url = f"{BASE_DOCUMENT_URL}{doc_id}_multi/xml"
    save_path = os.path.join(local_dir_path, f"{title}.xml")
    
    download_file(download_url, save_path)

def download_file(url, save_path):
    """Download a file with retry logic."""
    if os.path.exists(save_path):
        logger.info(f"File already exists, skipping: {save_path}")
        return True
    
    logger.info(f"Downloading {url} to {save_path}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded: {save_path}")
            # Add a small delay to avoid overwhelming the server
            time.sleep(RATE_LIMIT_DELAY)
            return True
        
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt+1}/{MAX_RETRIES} failed for {url}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"Failed to download {url} after {MAX_RETRIES} attempts")
                return False

def main():
    """Entry point for the scraper."""
    logger.info("Starting BC Laws XML Scraper")
    
    try:
        # Start with the root URL
        process_directory(BASE_CONTENT_URL, ROOT_DIR)
        logger.info("Scraping completed successfully")
    
    except Exception as e:
        logger.error(f"An error occurred during scraping: {str(e)}")

if __name__ == "__main__":
    main()
