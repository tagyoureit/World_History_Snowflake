#!/usr/bin/env python3
"""
World History Textbook PDF Downloader
Downloads all PDF chapters from https://glhssocialstudies.weebly.com/world-history-textbook---pdf-copy.html
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse
import re
from tqdm import tqdm


class PDFDownloader:
    def __init__(self, base_url, download_dir="world_history_pdfs"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        # Set headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create download directory
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    def get_pdf_links(self):
        """Extract all PDF download links from the webpage"""
        print(f"Fetching PDF links from {self.base_url}")
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links that point to PDF files
            pdf_links = []
            
            # Look for direct PDF links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.lower().endswith('.pdf'):
                    # Convert relative URLs to absolute
                    full_url = urljoin(self.base_url, href)
                    pdf_links.append({
                        'url': full_url,
                        'text': link.get_text(strip=True),
                        'filename': os.path.basename(urlparse(href).path)
                    })
            
            # Also look for any embedded or referenced PDFs in the content
            # Some sites use different patterns
            content_text = soup.get_text()
            
            print(f"Found {len(pdf_links)} PDF links")
            return pdf_links
            
        except requests.RequestException as e:
            print(f"Error fetching webpage: {e}")
            return []
    
    def download_pdf(self, pdf_info):
        """Download a single PDF file"""
        url = pdf_info['url']
        filename = pdf_info['filename']
        
        # Clean filename for filesystem
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        filepath = os.path.join(self.download_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            print(f"File already exists: {filename}")
            return True
        
        try:
            print(f"Downloading: {filename}")
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Get file size for progress bar
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            print(f"Successfully downloaded: {filename}")
            return True
            
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return False
    
    def download_all_pdfs(self):
        """Download all PDFs from the website"""
        pdf_links = self.get_pdf_links()
        
        if not pdf_links:
            print("No PDF links found. Let me try a different approach...")
            # Try alternative scraping methods for Weebly sites
            return self.alternative_scraping()
        
        successful_downloads = 0
        failed_downloads = 0
        
        for i, pdf_info in enumerate(pdf_links, 1):
            print(f"\nDownloading {i}/{len(pdf_links)}: {pdf_info['text']}")
            
            if self.download_pdf(pdf_info):
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            # Be respectful to the server
            time.sleep(1)
        
        print(f"\nDownload completed!")
        print(f"Successful: {successful_downloads}")
        print(f"Failed: {failed_downloads}")
        print(f"Files saved to: {os.path.abspath(self.download_dir)}")
        
        return successful_downloads > 0
    
    def alternative_scraping(self):
        """Alternative method for Weebly sites that might have different structure"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            # Look for common Weebly patterns
            # Often PDFs are hosted on external services or have specific patterns
            content = response.text
            
            # Look for common PDF hosting patterns
            pdf_patterns = [
                r'https?://[^"\s]+\.pdf',
                r'/files/[^"\s]+\.pdf',
                r'uploads/[^"\s]+\.pdf'
            ]
            
            found_urls = set()
            for pattern in pdf_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Clean up the URL
                    url = match.strip('"\'')
                    if url.startswith('/'):
                        url = urljoin(self.base_url, url)
                    found_urls.add(url)
            
            if found_urls:
                print(f"Found {len(found_urls)} PDF URLs using alternative method")
                pdf_links = []
                for i, url in enumerate(found_urls, 1):
                    filename = f"chapter_{i:02d}.pdf"
                    if '/' in url:
                        filename = os.path.basename(urlparse(url).path)
                    
                    pdf_links.append({
                        'url': url,
                        'text': f'Chapter {i}',
                        'filename': filename
                    })
                
                # Download using the found URLs
                successful_downloads = 0
                for pdf_info in pdf_links:
                    if self.download_pdf(pdf_info):
                        successful_downloads += 1
                    time.sleep(1)
                
                return successful_downloads > 0
            
            print("No PDF URLs found with alternative methods either.")
            return False
            
        except Exception as e:
            print(f"Error in alternative scraping: {e}")
            return False


def main():
    url = "https://glhssocialstudies.weebly.com/world-history-textbook---pdf-copy.html"
    
    downloader = PDFDownloader(url)
    success = downloader.download_all_pdfs()
    
    if success:
        print(f"\nPDFs are ready for upload to Snowflake!")
        print(f"Download directory: {os.path.abspath(downloader.download_dir)}")
    else:
        print("\nManual intervention may be required. Check the website structure.")


if __name__ == "__main__":
    main() 