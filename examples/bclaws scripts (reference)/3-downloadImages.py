import os
import re
import time
import requests
import certifi
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def download_images_from_html(base_url, source_folder, output_folder, delay=1):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    session.verify = certifi.where()  # Use certifi's certificates

    # Ensure the base output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Walk through all directories and files in the source folder
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')
                    images = soup.find_all('img')

                    image_paths = []

                    for img in images:
                        src = img.get('src')
                        if src and "statreg/" in src:
                            image_name = src.split("statreg/")[-1]

                            if re.match(r'^\d', image_name):
                                image_url = urljoin(base_url, src)
                                image_path = os.path.join(root.replace(source_folder, '').strip(os.sep), file[:-5], image_name)
                                image_paths.append((image_url, image_path))

                    if image_paths:
                        output_dir_for_file = os.path.join(output_folder, root.replace(source_folder, '').strip(os.sep), file[:-5])
                        os.makedirs(output_dir_for_file, exist_ok=True)

                        for image_url, image_path in image_paths:
                            full_image_path = os.path.join(output_folder, image_path)

                            # Check if the image already exists before downloading
                            if not os.path.exists(full_image_path):
                                try:
                                    response = session.get(image_url)
                                    if response.status_code == 200:
                                        with open(full_image_path, 'wb') as img_file:
                                            img_file.write(response.content)
                                    else:
                                        print(f"Failed to download {image_url}: {response.status_code}")
                                    time.sleep(delay)  # Delay between downloads
                                except requests.RequestException as e:
                                    print(f"Error during requests to {image_url}: {str(e)}")
                                    time.sleep(delay * 5)  # Longer sleep on error
                            else:
                                print(f"Skipping download, file already exists: {full_image_path}")

def main():
    BASE_URL = "https://www.bclaws.gov.bc.ca"
    SOURCE_FOLDER = "./html/Cleaned"
    OUTPUT_FOLDER = "./images"
    DELAY = 1.5  # seconds

    download_images_from_html(BASE_URL, SOURCE_FOLDER, OUTPUT_FOLDER, DELAY)

if __name__ == "__main__":
    main()
