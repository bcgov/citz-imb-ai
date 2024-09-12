import os
import re

def format_text(content):
    content = re.sub(r'(\S+:\n)(?=\S)', r'\1\n', content)
    content = '\n'.join(line.capitalize() for line in content.split('\n'))

    lines = content.split('\n')
    consolidated_lines = []
    current_line = ""
    for line in lines:
        if line.endswith(('.', '?', '!', ':')) or line.istitle():
            if current_line:
                consolidated_lines.append(current_line.strip() + " " + line)
                current_line = ""
            else:
                consolidated_lines.append(line)
        else:
            current_line += " " + line if current_line else line

    if current_line:
        consolidated_lines.append(current_line)

    return '\n'.join(consolidated_lines)

def remove_extra_whitespace(file_path, output_path):
    with open(file_path, 'r') as file:
        content = file.read()

    cleaned_content = '\n'.join(line.strip() for line in content.split('\n') if line.strip())
    formatted_content = format_text(cleaned_content)

    with open(output_path, 'w') as file:
        file.write(formatted_content)

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
                remove_extra_whitespace(source_path, destination_path)

source_folder = 'txt'
destination_folder = 'NoWhitespace'

process_folder(source_folder, destination_folder)
