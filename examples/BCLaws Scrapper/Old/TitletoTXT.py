import re
import os

def extract_titles_from_folder(input_folder, output_file):
    # Regular expression to find <act:title> tags and capture their content
    pattern = r'<act:title>(.*?)</act:title>'

    all_titles = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.xml'):
            file_path = os.path.join(input_folder, filename)
            with open(file_path, 'r') as infile:
                content = infile.read()
                titles = re.findall(pattern, content)
                all_titles.extend(titles)

    # Sort the list of titles alphabetically
    all_titles.sort()

    with open(output_file, 'w') as outfile:
        for title in all_titles:
            outfile.write(title + '\n')

# Example usage
input_folder = 'xml/Final/Acts'
output_file = 'all_act_titles.txt'
extract_titles_from_folder(input_folder, output_file)
