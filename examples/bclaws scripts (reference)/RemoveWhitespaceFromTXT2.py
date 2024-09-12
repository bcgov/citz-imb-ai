import os

def remove_all_blank_lines(file_path, output_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # Remove all blank lines
    cleaned_content = [line for line in content if line.strip()]

    with open(output_path, 'w', encoding='utf-8') as file:
        file.writelines(cleaned_content)

def process_folder(source_folder, destination_folder):
    os.makedirs(destination_folder, exist_ok=True)

    for root, dirs, files in os.walk(source_folder):
        # Create corresponding subdirectories in the destination folder
        for dir in dirs:
            os.makedirs(os.path.join(destination_folder, os.path.relpath(os.path.join(root, dir), source_folder)), exist_ok=True)

        for filename in files:
            if filename.endswith('.txt'):
                source_path = os.path.join(root, filename)
                relative_path = os.path.relpath(root, source_folder)
                destination_path = os.path.join(destination_folder, relative_path, filename)
                remove_all_blank_lines(source_path, destination_path)

source_folder = 'txt2'
destination_folder = 'NoWhitespace2'

process_folder(source_folder, destination_folder)
