import os
from bs4 import BeautifulSoup

def html_to_text(input_folder, output_folder):
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Loop through all files and folders in the input folder
    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            if filename.endswith('.html'):
                input_file_path = os.path.join(root, filename)

                # Calculate the relative path to maintain the folder structure
                relative_path = os.path.relpath(root, input_folder)
                output_subfolder = os.path.join(output_folder, relative_path)
                os.makedirs(output_subfolder, exist_ok=True)

                output_file_path = os.path.join(output_subfolder, filename.replace('.html', '.txt'))

                with open(input_file_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text()

                # Remove leading and trailing whitespace from each line
                cleaned_text = '\n'.join(line.strip() for line in text.splitlines())

                with open(output_file_path, 'w', encoding='utf-8') as file:
                    file.write(cleaned_text)

                print(f'Converted {input_file_path} to plain text at {output_file_path}.')

if __name__ == '__main__':
    input_folder = 'html'  # Path to the folder containing HTML files
    output_folder = 'txt2'  # Path to the folder where you want to save the text files
    html_to_text(input_folder, output_folder)
