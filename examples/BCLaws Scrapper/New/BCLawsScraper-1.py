import os
import requests
import xml.etree.ElementTree as ET
import time
import urllib.parse

# Configurable parameters
CONSOL_NUMBER = 43  # Change this to target different consolidations
SLOW_DOWN_SECONDS = 0.5  # Delay between requests (seconds)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Base URLs with dynamic consol number
CONTENT_API_BASE = f"https://www.bclaws.gov.bc.ca/civix/content/consol{CONSOL_NUMBER}/consol{CONSOL_NUMBER}/"

DOCUMENT_API_BASE = f"https://www.bclaws.gov.bc.ca/civix/document/id/consol{CONSOL_NUMBER}/consol{CONSOL_NUMBER}/"

# Create root folder in the same directory as the script
ROOT_FOLDER = os.path.join(SCRIPT_DIR, f"Consol{CONSOL_NUMBER}")

# Create root folder
os.makedirs(ROOT_FOLDER, exist_ok=True)

def download_file(url, save_path, max_retries=3):
    """Download a file from URL and save it to save_path"""
    retries = 0
    while retries < max_retries:
        try:
            print(f"Downloading: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Successfully saved to: {save_path}")
            # Add delay after successful download
            time.sleep(SLOW_DOWN_SECONDS)
            return True
        except Exception as e:
            retries += 1
            print(f"Error downloading {url}, retry {retries}/{max_retries}: {e}")
            time.sleep(1)  # Wait before retrying
            
            if retries == max_retries:
                print(f"Failed to download {url} after {max_retries} retries")
                return False

def get_xml_content(url, max_retries=3):
    """Get and parse XML content from a URL"""
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            # Add delay after successful request
            time.sleep(SLOW_DOWN_SECONDS)
            return ET.fromstring(response.content)
        except Exception as e:
            retries += 1
            print(f"Error accessing {url}, retry {retries}/{max_retries}: {e}")
            time.sleep(1)  # Wait before retrying
            
            if retries == max_retries:
                print(f"Failed to access {url} after {max_retries} retries")
                return None

def process_directory(directory_path="", physical_path=None):
    """
    Process a directory in the Content API recursively
    
    Args:
        directory_path: The API path to the directory
        physical_path: The local filesystem path to save files to
    """
    # If no physical path provided, use the root folder
    if physical_path is None:
        physical_path = ROOT_FOLDER
        
    # Create the directory if it doesn't exist
    os.makedirs(physical_path, exist_ok=True)
    
    # Construct the content API URL
    content_url = CONTENT_API_BASE + directory_path
    print(f"Processing directory: {content_url}")
    
    # Get the directory content
    root = get_xml_content(content_url)
    if root is None:
        return
    
    # First pass: Check for multi-part documents
    has_multi_document = False
    
    for doc in root.findall('.//document'):
        doc_ext_elem = doc.find('CIVIX_DOCUMENT_EXT')
        doc_order_elem = doc.find('CIVIX_DOCUMENT_ORDER')
        
        # Check if this is a table of contents (multi-document marker)
        if (doc_ext_elem is not None and doc_ext_elem.text == 'htm' and 
            doc_order_elem is not None and doc_order_elem.text == '0'):
            
            # Found a multi-document table of contents
            doc_id = doc.find('CIVIX_DOCUMENT_ID').text
            doc_title = doc.find('CIVIX_DOCUMENT_TITLE').text
            
            # Construct the multi-document URL (append _multi)
            document_url = f"{DOCUMENT_API_BASE}{doc_id}_multi/xml"
            
            # Create a safe filename
            safe_filename = f"{doc_title.replace('/', '_').replace('\\', '_')}.xml"
            save_path = os.path.join(physical_path, safe_filename)
            
            # Download the complete multi-document
            success = download_file(document_url, save_path)
            if success:
                print(f"Downloaded multi-document: {doc_title}")
                has_multi_document = True
                break
    
    # Second pass: Process directories and regular documents
    for element in root:
        tag_name = element.tag
        
        if tag_name == 'dir':
            # Handle directories recursively
            dir_id = element.find('CIVIX_DOCUMENT_ID').text
            dir_title = element.find('CIVIX_DOCUMENT_TITLE').text
            
            # Create safe directory name
            safe_dir_name = dir_title.replace('/', '_').replace('\\', '_')
            new_physical_path = os.path.join(physical_path, safe_dir_name)
            
            # Construct the new directory path for the API
            new_dir_path = dir_id if not directory_path else f"{directory_path}/{dir_id}"
            
            # Process the subdirectory
            process_directory(new_dir_path, new_physical_path)
            
        elif tag_name == 'document' and not has_multi_document:
            # Skip individual documents if we already have a multi-document
            doc_id = element.find('CIVIX_DOCUMENT_ID').text
            doc_title = element.find('CIVIX_DOCUMENT_TITLE').text
            doc_type = element.find('CIVIX_DOCUMENT_TYPE').text
            
            # Skip if not a document or if it's a table of contents (htm)
            if doc_type != 'document':
                continue
                
            doc_ext_elem = element.find('CIVIX_DOCUMENT_EXT')
            if doc_ext_elem is None or doc_ext_elem.text != 'xml':
                continue
            
            # Process regular XML document
            document_url = f"{DOCUMENT_API_BASE}{doc_id}/xml"
            
            # Create a safe filename
            safe_filename = f"{doc_title.replace('/', '_').replace('\\', '_')}.xml"
            save_path = os.path.join(physical_path, safe_filename)
            
            # Download the file
            success = download_file(document_url, save_path)
            if success:
                print(f"Downloaded document: {doc_title}")

# Start the scraping process
if __name__ == "__main__":
    print(f"Starting BC Laws scraper for consol{CONSOL_NUMBER} content")
    print(f"Files will be saved to: {os.path.abspath(ROOT_FOLDER)}")
    print(f"Using a delay of {SLOW_DOWN_SECONDS} seconds between requests")
    process_directory()
    print("Scraping completed")
