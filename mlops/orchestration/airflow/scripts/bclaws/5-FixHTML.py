import os
from bs4 import BeautifulSoup
import re

def fix_html_files(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                fix_html(file_path)

def fix_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Remove nested <p> tags
    html_content = re.sub(r'<p[^>]*>\s*<p', '<p', html_content)
    html_content = re.sub(r'</p>\s*</p>', '</p>', html_content)
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Fix <p> tags containing block-level elements
    for p in soup.find_all('p'):
        if p.find(['div', 'p']):
            new_tag = soup.new_tag('div')
            new_tag.extend(p.contents)
            p.replace_with(new_tag)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))
    
    print(f"Fixed: {file_path}")

if __name__ == "__main__":
    directory_path = os.path.join(os.path.dirname(__file__), "html")
    fix_html_files(directory_path)
