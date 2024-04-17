import os
from bs4 import BeautifulSoup

def extract_and_save_tables(input_directory, output_directory):
    # Ensure the output directory exists, create if it doesn't
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Loop through all files in the specified input directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".html"):
            file_path = os.path.join(input_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                
                # Find the title div and store it
                title_div = soup.find('div', id='title')
                
                # Find all table tags
                tables = soup.find_all('table')
                if not tables:
                    # If no tables are found, continue to the next file
                    continue

                table_count = 1
                
                for table in tables:
                    # Find the section div that precedes the current table
                    section_div = table.find_previous('div', class_='section')
                    
                    # Prepare the new soup
                    new_soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
                    new_body = new_soup.find('body')
                    
                    # Add the title and section divs to the new file
                    if title_div:
                        new_body.append(title_div)
                    if section_div:
                        new_body.append(section_div)
                    
                    # Add the current table
                    new_body.append(table)
                    
                    # Create new file for each table
                    new_filename = f"{filename.split('.')[0]}_table_{table_count}.html"
                    new_file_path = os.path.join(output_directory, new_filename)
                    with open(new_file_path, 'w', encoding='utf-8') as new_file:
                        new_file.write(str(new_soup))
                    table_count += 1

# Provide the directory containing your HTML files
input_directory = './test/html'
output_directory = './test/tables'
extract_and_save_tables(input_directory, output_directory)
