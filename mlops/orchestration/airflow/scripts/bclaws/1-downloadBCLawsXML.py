import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
import aiofiles

BASE_URL = "https://www.bclaws.gov.bc.ca/civix/content/complete/statreg/"

async def fetch_content(url, session):
    try:
        async with session.get(url) as response:
            content = await response.text()
            return BeautifulSoup(content, 'xml')
    except Exception as error:
        print(f"Error fetching URL {url}: {str(error)}")
        return None

async def download_xml(url, filename, session):
    try:
        async with session.get(url) as response:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            async with aiofiles.open(filename, 'wb') as writer:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await writer.write(chunk)
    except Exception as error:
        print(f"Error downloading file {url}: {str(error)}")

async def process_directory(url, session, depth=0):
    soup = await fetch_content(url, session)
    if not soup:
        return

    dirs = soup.find_all('dir')
    for elem in dirs:
        document_status = elem.find('CIVIX_DOCUMENT_STATUS')
        if document_status and document_status.text == 'Repealed':
            continue
        document_id = elem.find('CIVIX_DOCUMENT_ID')
        if not document_id:
            continue
        next_url = f"{BASE_URL}{'/' * depth}{document_id.text}"
        await process_directory(next_url, session, depth + 1)

    documents = soup.find_all('document')
    for elem in documents:
        document_id = elem.find('CIVIX_DOCUMENT_ID').text
        document_title = elem.find('CIVIX_DOCUMENT_TITLE').text
        document_ext = elem.find('CIVIX_DOCUMENT_EXT').text
        
        if document_ext == 'htm':
            download_url = f"https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/{document_id}_multi/xml"
        elif document_ext == 'xml':
            download_url = f"https://www.bclaws.gov.bc.ca/civix/document/id/complete/statreg/{document_id}/xml"
        else:
            continue

        sanitized_title = ''.join(c if c.isalnum() or c.isspace() else '_' for c in document_title).replace(' ', '_')
        filename = os.path.join(
            os.path.dirname(__file__),
            "xml",
            f"{sanitized_title}.{'multi.xml' if document_ext == 'htm' else 'xml'}"
        )
        await download_xml(download_url, filename, session)

async def main():
    async with aiohttp.ClientSession() as session:
        await process_directory(BASE_URL, session)
    print("Download completed.")

if __name__ == "__main__":
    asyncio.run(main())
