import os
import re
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Prettify the HTML first
    formatter = HTMLFormatter(indent=3)
    soup = BeautifulSoup(content, 'html.parser')
    content = soup.prettify(formatter=formatter)

    # Remove the XML declaration
    content = re.sub(r'<\?xml version="1.0" encoding="UTF-8"\?>', '', content, flags=re.DOTALL)

    # Remove the DOCTYPE declaration
    content = re.sub(r'<!DOCTYPE html[^>]*>', '', content)

    # Remove the <head> element and its content
    content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL)

    # Remove attributes from the opening <html> tag
    content = re.sub(r'<html[^>]*>', '<html>', content)

    # Remove attributes from the opening <body> tag
    content = re.sub(r'<body[^>]*>', '<body>', content)

    # Remove the <div id="toolBar"> element and its contents
    content = re.sub(r'<div id="toolBar"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    
    # Remove the <div id="header"> element and its contents
    content = re.sub(r'<div id="header"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    
    # Remove the <div id="act:currency"> element and its contents
    content = re.sub(r'<div id="act:currency"[^>]*>.*?</div>', '', content, flags=re.DOTALL)
    
    # Remove the <div id="contents"> element and its contents
    content = re.sub(r'<div id="contents"[^>]*>.*?</div>', '', content, flags=re.DOTALL)

    # Remove the <p class="copyright"> element and its contents
    content = re.sub(r'<p class="copyright"[^>]*>.*?</p>', '', content, flags=re.DOTALL)

    # Prettify the HTML again
    soup = BeautifulSoup(content, 'html.parser')
    content = soup.prettify(formatter=formatter)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def process_downloads_folder(downloads_folder):
    for filename in os.listdir(downloads_folder):
        file_path = os.path.join(downloads_folder, filename)
        if os.path.isfile(file_path) and file_path.endswith('.html'):
            process_file(file_path)
            print(f'Processed {filename}')

downloads_folder = 'html'
process_downloads_folder(downloads_folder)
