import os
import requests
import xml.etree.ElementTree as ET
import time
import urllib.parse
import re
from bs4 import BeautifulSoup

# ----- CONFIGURABLE SETTINGS -----
# Delay between requests in seconds (increase to be gentler on the server)
SLOW_DOWN_SECONDS = 0

# Set to True to download all consolidations, False to just list them
DOWNLOAD_ALL = False

# ----- END CONFIGURABLE SETTINGS -----

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_available_consolidations():
    """
    Fetch and parse the archive page to get all available consolidations
    Returns a list of tuples: [(path, name), ...]
    """
    try:
        # Fetch the archive page
        archive_url = "https://www.bclaws.gov.bc.ca/archive-stat.html"
        response = requests.get(archive_url, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all consolidation links
        consolidations = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            match = re.search(r'(?:^|/)civix/content/(consol\d+[a-z]?/consol\d+[a-z]?)/', href)
            if match:
                path = match.group(1)
                name = link.text.strip()
                # Only include links that start with "Consol "
                if name.startswith("Consol "):
                    consolidations.append((path, name))
        
        print(f"Found {len(consolidations)} consolidations")
        return consolidations
        
    except Exception as e:
        print(f"Error fetching consolidations: {e}")
        return []

def download_file(url, save_path, max_retries=3):
    """Download a file from URL and save it to save_path if it doesn't already exist"""
    # Check if file already exists
    if os.path.exists(save_path):
        print(f"File already exists, skipping: {save_path}")
        return True
        
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

def process_directory(content_api_base, document_api_base, root_folder, directory_path="", physical_path=None):
    """
    Process a directory in the Content API recursively
    
    Args:
        content_api_base: Base URL for content API
        document_api_base: Base URL for document API
        root_folder: Local folder to save files to
        directory_path: The API path to the directory
        physical_path: The local filesystem path to save files to
    """
    # If no physical path provided, use the root folder
    if physical_path is None:
        physical_path = root_folder
        
    # Create the directory if it doesn't exist
    os.makedirs(physical_path, exist_ok=True)
    
    # Construct the content API URL
    content_url = content_api_base + directory_path
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
            document_url = f"{document_api_base}{doc_id}_multi/xml"
            
            # Create a safe filename
            safe_filename = f"{doc_title.replace('/', '_').replace('\\', '_')}.xml"
            save_path = os.path.join(physical_path, safe_filename)
            
            # Download the complete multi-document if it doesn't already exist
            success = download_file(document_url, save_path)
            if success:
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
            process_directory(content_api_base, document_api_base, root_folder, new_dir_path, new_physical_path)
            
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
            document_url = f"{document_api_base}{doc_id}/xml"
            
            # Create a safe filename
            safe_filename = f"{doc_title.replace('/', '_').replace('\\', '_')}.xml"
            save_path = os.path.join(physical_path, safe_filename)
            
            # Download the file if it doesn't already exist
            download_file(document_url, save_path)

def process_consolidation(consol_path, consol_name):
    """Process a single consolidation"""
    print(f"\n{'='*80}")
    print(f"Processing {consol_name}")
    print(f"{'='*80}")
    
    # Use the full consolidation name for the folder (sanitized for file system)
    safe_folder_name = consol_name.replace('/', '_').replace('\\', '_').replace(':', '-')
    
    # Set up the URLs for this consolidation
    content_api_base = f"https://www.bclaws.gov.bc.ca/civix/content/{consol_path}/"
    document_api_base = f"https://www.bclaws.gov.bc.ca/civix/document/id/{consol_path}/"
    
    # Create root folder in the same directory as the script
    root_folder = os.path.join(SCRIPT_DIR, safe_folder_name)
    
    # Create root folder
    os.makedirs(root_folder, exist_ok=True)
    
    print(f"Content API: {content_api_base}")
    print(f"Document API: {document_api_base}")
    print(f"Files will be saved to: {os.path.abspath(root_folder)}")
    print(f"Using a delay of {SLOW_DOWN_SECONDS} seconds between requests")
    
    # Start the directory processing
    process_directory(content_api_base, document_api_base, root_folder)
    
    print(f"Completed processing {consol_name}")

# Start the scraping process
if __name__ == "__main__":
    print(f"Starting BC Laws scraper for all consolidations")
    print(f"Using a delay of {SLOW_DOWN_SECONDS} seconds between requests")
    
    # Get all available consolidations
    consolidations = get_available_consolidations()
    
    if not consolidations:
        print("No consolidations found. Please check the archive URL or try again later.")
    else:
        # Display available consolidations
        print("\nAvailable consolidations:")
        for i, (path, name) in enumerate(consolidations, 1):
            print(f"{i}. {name} ({path})")
        
        if DOWNLOAD_ALL:
            # Process all consolidations
            print(f"\nProceeding to download all {len(consolidations)} consolidations")
            for path, name in consolidations:
                process_consolidation(path, name)
            print("\nAll consolidations have been processed!")
        else:
            print("\nDownload disabled. Set DOWNLOAD_ALL = True to download all consolidations.")
    
    print("\nScraping completed")
