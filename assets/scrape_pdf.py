"""
PDF Downloader for PB Guitar Studio Lesson PDFs
Downloads all PDF files referenced at: https://www.pbguitarstudio.com/GuitarLessonPDF.html
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path

# Configuration
BASE_URL = "https://www.pbguitarstudio.com/GuitarLessonPDF.html"
OUTPUT_DIR = os.path.expanduser("~/Guitar_Lesson_PDFs")
DELAY_BETWEEN_DOWNLOADS = 0.5  # seconds (be respectful to the server)

# Categories to exclude
EXCLUDED_CATEGORIES = [
    "Guitar Grid & TAB sheets:",
    "Blank Sheet Music Paper:",
    "Basic Basics:",
    "Important Worksheets:"
]

# Create user-agent header to be respectful
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def create_output_directory():
    """Create the output directory if it doesn't exist."""
    try:
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        print(f"✅ Output directory ready: {OUTPUT_DIR}\n")
        return True
    except Exception as e:
        print(f"❌ Error creating directory: {e}")
        return False


def fetch_page(url):
    """Fetch the webpage and return BeautifulSoup object."""
    try:
        print(f"🔍 Fetching page: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        print("✅ Page fetched successfully\n")
        return soup
    except Exception as e:
        print(f"❌ Error fetching page: {e}")
        return None


def extract_pdf_links(soup, base_url):
    """Extract all PDF links from the page, excluding specified categories."""
    pdf_links = []
    
    try:
        # Track current category
        current_category = None
        excluded = False
        
        # Get all elements to parse in order
        # Look for headings (h1-h6) and links
        all_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a'])
        
        for element in all_elements:
            # Check if this is a heading (category marker)
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                heading_text = element.get_text(strip=True)
                current_category = heading_text
                
                # Check if this category is in the excluded list
                excluded = any(excluded_cat.lower() in heading_text.lower() for excluded_cat in EXCLUDED_CATEGORIES)
                
                if not excluded and heading_text:
                    print(f"📚 Category: {heading_text}")
            
            # Process links if not in an excluded category
            elif element.name == 'a' and not excluded:
                href = element.get('href')
                link_text = element.get_text(strip=True)
                
                # Check if link points to a PDF
                if href and ('.pdf' in href.lower() or 'pdf' in link_text.lower()):
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(base_url, href)
                    filename = os.path.basename(urlparse(absolute_url).path)
                    
                    # Only add if filename is not empty
                    if filename:
                        pdf_links.append({
                            'url': absolute_url,
                            'text': link_text,
                            'filename': filename,
                            'category': current_category
                        })
        
        if pdf_links:
            print(f"\n📄 Found {len(pdf_links)} PDF(s) (excluding specified categories):\n")
            
            # Display by category
            current_cat = None
            for pdf in pdf_links:
                if pdf['category'] != current_cat:
                    current_cat = pdf['category']
                    print(f"  📚 {current_cat}")
                
                print(f"    • {pdf['text']}")
        else:
            print("❌ No PDF links found (all may have been excluded)")
        
        return pdf_links
        
    except Exception as e:
        print(f"❌ Error extracting PDF links: {e}")
        return []


def download_pdf(pdf_url, filename, output_dir):
    """Download a single PDF file."""
    try:
        output_path = os.path.join(output_dir, filename)
        
        print(f"⬇️  Downloading: {filename}...", end=" ")
        
        response = requests.get(pdf_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Write the PDF file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(output_path)
        print(f"✅ ({file_size:,} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def download_all_pdfs(pdf_links, output_dir):
    """Download all PDF files."""
    if not pdf_links:
        print("❌ No PDFs to download")
        return 0
    
    print(f"📥 Starting downloads to: {output_dir}\n")
    
    successful = 0
    failed = 0
    
    for i, pdf in enumerate(pdf_links, 1):
        print(f"[{i}/{len(pdf_links)}] ", end="")
        
        success = download_pdf(pdf['url'], pdf['filename'], output_dir)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Be respectful to the server - add delay between requests
        if i < len(pdf_links):
            time.sleep(DELAY_BETWEEN_DOWNLOADS)
    
    print(f"\n{'='*50}")
    print(f"✅ Successfully downloaded: {successful}")
    print(f"❌ Failed downloads: {failed}")
    print(f"📁 Files saved to: {output_dir}")
    print(f"{'='*50}\n")
    
    return successful


def main():
    """Main function to orchestrate the PDF download process."""
    print("="*50)
    print("🎸 Guitar Lesson PDF Downloader")
    print("="*50 + "\n")
    
    # Create output directory
    if not create_output_directory():
        return
    
    # Fetch the page
    soup = fetch_page(BASE_URL)
    if not soup:
        return
    
    # Extract PDF links
    pdf_links = extract_pdf_links(soup, BASE_URL)
    if not pdf_links:
        return
    
    # Confirm before downloading
    user_input = input(f"Download {len(pdf_links)} PDF(s)? (yes/no): ").strip().lower()
    if user_input not in ['yes', 'y']:
        print("❌ Download cancelled")
        return
    
    print()
    
    # Download all PDFs
    successful = download_all_pdfs(pdf_links, OUTPUT_DIR)
    
    if successful > 0:
        print(f"🎉 Perfect! Your guitar lesson PDFs are ready to use!\n")


if __name__ == "__main__":
    main()
