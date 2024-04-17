import os
from bs4 import BeautifulSoup

def extract_and_save_tables(input_directory, output_directory):
    # Ensure the output directory exists, create if it doesn't
    os.makedirs(output_directory, exist_ok=True)

    # Loop through all files and subdirectories in the specified input directory
    for root, dirs, files in os.walk(input_directory):
        for filename in files:
            if filename.endswith(".html"):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', encoding='utf-8') as html_file:
                    soup = BeautifulSoup(html_file, 'html.parser')

                    # Find the title div and store it
                    title_div = soup.find('div', id='title')

                    # Check for and store the actname div if it exists
                    actname_div = soup.find('div', id='actname')

                    # Find all table tags
                    tables = soup.find_all('table')
                    if not tables:
                        # If no tables are found, continue to the next file
                        continue

                    # Create a corresponding subdirectory in the destination folder
                    relative_path = os.path.relpath(root, input_directory)
                    output_subdirectory = os.path.join(output_directory, relative_path)
                    os.makedirs(output_subdirectory, exist_ok=True)

                    table_count = 1

                    for table in tables:
                        # Prepare the new soup
                        new_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
                        new_body = new_soup.find('body')

                        # Add the title, actname (if exists), and table to the new file
                        if title_div:
                            new_body.append(title_div)
                        if actname_div:
                            new_body.append(actname_div)
                        new_body.append(table)

                        # Create new file for each table
                        new_filename = f"{filename.split('.')[0]}_table_{table_count}.html"
                        new_file_path = os.path.join(output_subdirectory, new_filename)
                        with open(new_file_path, 'w', encoding='utf-8') as new_file:
                            new_file.write(str(new_soup))
                        table_count += 1

# Provide the directory containing your HTML files
input_directory = './html'
output_directory = './test/tables'
extract_and_save_tables(input_directory, output_directory)
