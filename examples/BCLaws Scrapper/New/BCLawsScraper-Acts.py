import os
import requests
import xml.etree.ElementTree as ET
import time
import urllib.parse
import re
import shutil
from bs4 import BeautifulSoup

# Delay between requests in seconds
SLOW_DOWN_SECONDS = 0

# Set to True to download all consolidations, False to select specific one(s)
DOWNLOAD_ALL = False

# Set to True to reorganize files after download
REORGANIZE_FILES = True

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the base directories for storing consolidations
CONSOLIDATIONS_DIR = os.path.join(SCRIPT_DIR, "Consolidations")
ACTS_DIR = os.path.join(CONSOLIDATIONS_DIR, "Acts")

# Function to sanitize filenames
def sanitize_filename(filename):
    # Replace consecutive whitespace with a single space
    sanitized = re.sub(r'\s+', ' ', filename)
    # Replace other problematic characters
    sanitized = sanitized.replace('/', '_').replace('\\', '_').replace(':', ' -')
    return sanitized.strip()

# Function to reorganize files and sanitize filenames
def reorganize_act_files(root_folder):
    """
    Traverse through directories and:
    1. Find files in 'Act' folders with names starting with 'Table of Contents - ',
       rename them, move them up one directory level, and remove empty Act folders.
    2. Remove empty media folders and their subdirectories
    3. Sanitize filenames by removing consecutive spaces
    """
    print(f"\n{'='*80}")
    print(f"Reorganizing files and sanitizing filenames in {root_folder}")
    print(f"{'='*80}")
    
    # Statistics for reporting
    act_folders = []
    media_folders = []
    files_processed = 0
    renamed_files = 0
    
    # Walk through the directory tree
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=False):  # Use topdown=False to process subdirectories first
        base_dir_name = os.path.basename(dirpath)
        
        # Check if current folder is named "Act"
        if base_dir_name == "Act":
            act_folders.append(dirpath)
            
            # Process files in the Act folder
            for filename in filenames:
                if filename.startswith("Table of Contents - "):
                    # Full path to the original file
                    original_file = os.path.join(dirpath, filename)
                    
                    # New filename without the prefix and sanitized
                    new_filename = sanitize_filename(filename.replace("Table of Contents - ", ""))
                    
                    # Parent directory of the Act folder
                    parent_dir = os.path.dirname(dirpath)
                    
                    # Full path for the destination file
                    destination_file = os.path.join(parent_dir, new_filename)
                    
                    print(f"Moving and renaming: {original_file} ? {destination_file}")
                    
                    # Move and rename the file
                    shutil.move(original_file, destination_file)
                    files_processed += 1
        
        # Track media folders
        if base_dir_name == "media" and dirpath.split(os.path.sep)[-2] not in ("media", "images"):
            media_folders.append(dirpath)
        
        # Sanitize all filenames
        for filename in filenames:
            sanitized_filename = sanitize_filename(filename)
            # Only rename if the sanitized filename is different
            if sanitized_filename != filename:
                old_path = os.path.join(dirpath, filename)
                new_path = os.path.join(dirpath, sanitized_filename)
                try:
                    # Avoid collision by checking if target file exists
                    if os.path.exists(new_path):
                        print(f"Cannot rename: {new_path} already exists")
                        continue
                    os.rename(old_path, new_path)
                    print(f"Renamed: {filename} ? {sanitized_filename}")
                    renamed_files += 1
                except Exception as e:
                    print(f"Error renaming {filename}: {e}")
    
    # After processing all files, check and remove empty Act folders
    folders_removed = 0
    for act_folder in act_folders:
        # Check if the folder is empty (no files or subdirectories)
        if not os.listdir(act_folder):
            print(f"Removing empty Act folder: {act_folder}")
            os.rmdir(act_folder)
            folders_removed += 1
    
    # Remove media folders and their subdirectories
    media_folders_removed = 0
    for media_folder in media_folders:
        try:
            print(f"Removing media folder and subdirectories: {media_folder}")
            shutil.rmtree(media_folder)
            media_folders_removed += 1
        except Exception as e:
            print(f"Error removing media folder {media_folder}: {e}")
    
    print(f"Reorganization complete:")
    print(f"- {files_processed} files processed")
    print(f"- {renamed_files} files renamed")
    print(f"- {folders_removed} empty Act folders removed")
    print(f"- {media_folders_removed} media folders and their subdirectories removed")
    
    return files_processed, renamed_files, folders_removed, media_folders_removed

# Function to just do cleanup without downloading
def do_cleanup_only():
    print("\nPerforming cleanup only (no downloads)")
    total_files = 0
    total_renamed_files = 0
    total_folders = 0
    total_media_folders = 0
    
    # Look for existing consolidation folders
    for item in os.listdir(ACTS_DIR):
        folder_path = os.path.join(ACTS_DIR, item)
        if os.path.isdir(folder_path):
            print(f"\nReorganizing and cleaning up {item}...")
            files, renamed, folders, media = reorganize_act_files(folder_path)
            total_files += files
            total_renamed_files += renamed
            total_folders += folders
            total_media_folders += media
    
    print(f"\nCleanup summary:")
    print(f"- {total_files} files processed")
    print(f"- {total_renamed_files} files renamed")
    print(f"- {total_folders} empty Act folders removed")
    print(f"- {total_media_folders} media folders removed")

# Fetch and parse the archive page to get all available consolidations
def get_available_consolidations():
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
    
# Download a file from URL and save it to save_path if it doesn't already exist
def download_file(url, save_path, max_retries=3):
    # Check if file already exists
    if os.path.exists(save_path):
        print(f"File already exists, skipping: {save_path}")
        return True
    
    # Special case for document ID "11025_00_multi"
    if "/11025_00_multi/xml" in url:
        print(f"Detected special case for document ID 11025_00_multi")
        corrected_url = url.replace("/11025_00_multi/xml", "/00_11025_00_multi/xml")
        print(f"Using corrected URL: {corrected_url}")
        url = corrected_url
    
    # Perform the download
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

# Get and parse XML content from a URL
def get_xml_content(url, max_retries=3):
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

# Process a directory in the Content API recursively
def process_directory(content_api_base, document_api_base, root_folder, directory_path="", physical_path=None):
    """
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
            safe_filename = f"{sanitize_filename(doc_title)}.xml"
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
            safe_dir_name = sanitize_filename(dir_title)
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
            safe_filename = f"{sanitize_filename(doc_title)}.xml"
            save_path = os.path.join(physical_path, safe_filename)
            
            # Download the file if it doesn't already exist
            download_file(document_url, save_path)

# Process a single consolidation
def process_consolidation(consol_path, consol_name):
    print(f"\n{'='*80}")
    print(f"Processing {consol_name}")
    print(f"{'='*80}")
    
    # Use the full consolidation name for the folder (sanitized for file system)
    safe_folder_name = sanitize_filename(consol_name)
    
    # Set up the URLs for this consolidation
    content_api_base = f"https://www.bclaws.gov.bc.ca/civix/content/{consol_path}/"
    document_api_base = f"https://www.bclaws.gov.bc.ca/civix/document/id/{consol_path}/"
    
    # Create root folder in the structured Consolidations/Acts hierarchy
    root_folder = os.path.join(ACTS_DIR, safe_folder_name)
    
    # Create necessary directories
    os.makedirs(ACTS_DIR, exist_ok=True)
    os.makedirs(root_folder, exist_ok=True)
    
    print(f"Content API: {content_api_base}")
    print(f"Document API: {document_api_base}")
    print(f"Files will be saved to: {os.path.abspath(root_folder)}")
    print(f"Using a delay of {SLOW_DOWN_SECONDS} seconds between requests")
    
    # Start the directory processing
    process_directory(content_api_base, document_api_base, root_folder)
    
    # Reorganize files if enabled
    if REORGANIZE_FILES:
        reorganize_act_files(root_folder)
    
    print(f"Completed processing {consol_name}")

# Function to let user select consolidation(s)
def select_consolidations(consolidations):
    print("\nSelect which consolidation(s) to download:")
    print("Enter a single number, multiple numbers separated by commas, 'all' for all consolidations, or 'n' to skip downloads and just do cleanup")
    print("Example: '1' or '1,3,5' or 'all' or 'n'")
    
    while True:
        selection = input("\nYour selection: ")
        
        if selection.lower() == 'all':
            return consolidations
        
        if selection.lower() == 'n':
            return []
            
        try:
            # Split by commas and convert to integers
            indices = [int(idx.strip()) for idx in selection.split(',')]
            
            # Check if all indices are valid
            if all(1 <= idx <= len(consolidations) for idx in indices):
                # Convert 1-based indices to 0-based and return selected consolidations
                return [consolidations[idx-1] for idx in indices]
            else:
                print(f"Invalid selection. Please enter numbers between 1 and {len(consolidations)}")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas, 'all', or 'n'")

# Start the scraping process
if __name__ == "__main__":
    print(f"Starting BC Laws scraper for Acts consolidations")
    print(f"Using a delay of {SLOW_DOWN_SECONDS} seconds between requests")
    print(f"File reorganization is {'enabled' if REORGANIZE_FILES else 'disabled'}")
    print(f"Files will be stored in: {os.path.abspath(CONSOLIDATIONS_DIR)}")
    
    # Create the base directory structure
    os.makedirs(ACTS_DIR, exist_ok=True)
    
    # Option to skip directly to cleanup
    if not DOWNLOAD_ALL and REORGANIZE_FILES:
        print("\nOptions:")
        print("1. Download and process act consolidations")
        print("2. Cleanup only (no downloads)")
        
        choice = input("\nSelect option (1 or 2): ")
        if choice == '2':
            do_cleanup_only()
            print("\nCleanup completed")
            exit()
    
    # Get all available consolidations
    consolidations = get_available_consolidations()
    
    if not consolidations:
        print("No consolidations found. Please check the archive URL or try again later.")
    else:
        # Display available consolidations
        print("\nAvailable consolidations:")
        for i, (path, name) in enumerate(consolidations, 1):
            print(f"{i}. {name} ({path})")
        
        # Determine which consolidations to process
        if DOWNLOAD_ALL:
            # Use all consolidations
            selected_consolidations = consolidations
            print(f"\nProceeding to download all {len(consolidations)} consolidations")
        else:
            # Let user select consolidations
            selected_consolidations = select_consolidations(consolidations)
            
            if not selected_consolidations:
                print("\nNo consolidations selected, proceeding to cleanup only")
                if REORGANIZE_FILES:
                    do_cleanup_only()
                else:
                    print("Reorganization is disabled. Nothing to do.")
                print("\nScript completed")
                exit()
            else:
                print(f"\nProceeding to download {len(selected_consolidations)} selected consolidation(s)")
        
        # Process selected consolidations
        for path, name in selected_consolidations:
            process_consolidation(path, name)
        
        if selected_consolidations:
            print("\nAll selected consolidations have been processed!")

    print("\nScraping completed")
