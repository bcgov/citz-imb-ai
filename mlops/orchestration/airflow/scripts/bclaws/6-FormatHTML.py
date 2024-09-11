import os
from bs4 import BeautifulSoup
import html5lib

def prettify_html_files(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                prettify_html(file_path)

def prettify_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Parse the HTML using html5lib for better handling of malformed HTML
    soup = BeautifulSoup(html_content, 'html5lib')
    
    # Prettify the HTML
    prettified_html = soup.prettify()
    
    # Write the prettified HTML back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(prettified_html)
    
    print(f"Prettified: {file_path}")

if __name__ == "__main__":
    directory_path = os.path.join(os.path.dirname(__file__), "html")
    prettify_html_files(directory_path)
