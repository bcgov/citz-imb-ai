import os
import requests
from urllib.parse import urlparse

def download_files(urls, folder):
    # Create the folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)

    for url in urls:
        # Get the filename from the URL
        filename = os.path.basename(urlparse(url).path)
        
        # Full path for saving the file
        file_path = os.path.join(folder, filename)
        
        # Download the file
        response = requests.get(url)
        
        # Check if the download was successful
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Successfully downloaded: {filename}")
        else:
            print(f"Failed to download: {filename}")

# URLs for XSD files
xsd_urls = [
    "https://www.bclaws.gov.bc.ca/standards/act.xsd",
    "https://www.bclaws.gov.bc.ca/standards/regulation.xsd",
    "https://www.bclaws.gov.bc.ca/standards/bylaw.xsd"
]

# URLs for XSLT files
xslt_urls = [
    "https://www.bclaws.gov.bc.ca/standards/act-html.xsl",
    "https://www.bclaws.gov.bc.ca/standards/reg-html.xsl",
    "https://www.bclaws.gov.bc.ca/standards/bylaw.xsl"
]

# Download XSD files
download_files(xsd_urls, "xsd")

# Download XSLT files
download_files(xslt_urls, "xslt")

print("Download process completed.")
