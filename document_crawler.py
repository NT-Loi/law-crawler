import json
import requests
from bs4 import BeautifulSoup
import re
import os
from tqdm import tqdm
import logging

logging.basicConfig(
    filename='document_crawler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
from urllib.parse import urlparse, parse_qs

class VBPLCrawler:
    def __init__(self, output_dir="crawled_docs"):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = "https://vbpl.vn"
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def extract_item_id(self, url):
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'ItemID' in params:
            return params['ItemID'][0]
        return None

    def get_document_data(self, url):
        """
        Main entry point for crawling a single law document URL.
        """
        item_id = self.extract_item_id(url)
        if not item_id:
            return {"error": f"Invalid URL (no ItemID): {url}"}

        logging.info(f"Fetching structured content for ItemID {item_id}...")
        
        # 1. Fetch main page for body text
        try:
            main_resp = self.session.get(url, headers=self.headers, timeout=30)
            main_resp.raise_for_status()
            main_soup = BeautifulSoup(main_resp.content, 'html.parser')
        except Exception as e:
            return {"error": f"Failed to fetch main page: {e}"}

        # 2. Fetch TOC page
        toc_url = f"{self.base_url}/VBQPPL_UserControls/Publishing_22/pMenuToanVan.aspx?IsVietNamese=True&ItemID={item_id}"
        try:
            # Note: VBPL TOC works with POST or GET. Let's try POST first as seen in their JS.
            toc_resp = self.session.post(toc_url, headers=self.headers, timeout=30)
            toc_resp.raise_for_status()
            toc_soup = BeautifulSoup(toc_resp.content, 'html.parser')
        except Exception as e:
            return {"error": f"Failed to fetch TOC: {e}"}

        # 3. Parse TOC
        # TOC links usually look like <a class='...' href='#Anchor'>Label</a>
        toc_items = []
        for link in toc_soup.select('a'):
            href = link.get('href', '')
            if href.startswith('#'):
                anchor = href[1:]
                label = link.get_text(strip=True)
                toc_items.append({
                    "anchor": anchor,
                    "label": label,
                    "type": link.get('class', ['unknown'])[0],
                    "title": link.get('title', '')
                })

        if not toc_items:
            # Fallback for old style TOC or empty TOC
            logging.warning(f"Warning: No TOC items found for {url}")

        # 4. Extract content from main page
        content_div = main_soup.select_one('#toanvancontent')
        if not content_div:
            content_div = main_soup.select_one('.toanvancontent')
        
        if not content_div:
            return {"error": "Main content div not found"}

        # Structuring strategy: Linear scan of descendants
        # Map anchor names to TOC indices
        anchor_to_index = {item['anchor']: i for i, item in enumerate(toc_items)}
        
        # Initialize content buffers
        section_buffers = [""] * len(toc_items)
        current_section_index = -1 # Before first anchor
        
        # We also need to see if exact IDs are used
        # We'll use a set of names/ids to trigger section changes
        
        for element in content_div.descendants:
            if element.name == 'a':
                # Check if this is a marker
                name = element.get('name')
                if name and name in anchor_to_index:
                    current_section_index = anchor_to_index[name]
                    continue
                
                # Check ID just in case
                eid = element.get('id')
                if eid and eid in anchor_to_index:
                    current_section_index = anchor_to_index[eid]
                    continue
            
            # Check for IDs on other elements
            if element.name and element.get('id') in anchor_to_index:
                current_section_index = anchor_to_index[element.get('id')]
            
            # If it's a text node, add to current section
            if isinstance(element, str) and current_section_index >= 0:
                text = element.strip()
                if text:
                    section_buffers[current_section_index] += text + " "
        
        # Verify if empty and try fallback (sometimes anchors are missing or capitalized differently)
        # But for now, trust the map.
        
        structured_sections = []
        for i, item in enumerate(toc_items):
            structured_sections.append({
                **item,
                "content": section_buffers[i].strip()
            })

        return {
            "item_id": item_id,
            "url": url,
            "title": main_soup.title.get_text(strip=True) if main_soup.title else "",
            "sections": structured_sections
        }

    def save_doc(self, data):
        if "error" in data:
            return
        filename = f"{data['item_id']}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def process_files(self, dieu_file, lienquan_file):
        """
        Reads URLs from the local JSON samples and crawls them.
        """
        urls = set()
        
        # Load Dieu.json
        if os.path.exists(dieu_file):
            try:
                with open(dieu_file, 'r', encoding='utf-8') as f:
                    dieus = json.load(f)
                    for d in dieus:
                        for ref in d.get('VBQPPL', []):
                            if ref.get('link') and 'vbpl.vn' in ref['link']:
                                urls.add(ref['link'])
            except Exception as e:
                logging.error(f"Error reading {dieu_file}: {e}")

        # Load LienQuan.json
        if os.path.exists(lienquan_file):
            try:
                with open(lienquan_file, 'r', encoding='utf-8') as f:
                    lqs = json.load(f)
                    for l in lqs:
                        if l.get('link') and 'vbpl.vn' in l['link']:
                            urls.add(l['link'])
            except Exception as e:
                logging.error(f"Error reading {lienquan_file}: {e}")

        logging.info(f"Found {len(urls)} unique VBPL URLs to crawl.")
        
        for url in tqdm(urls, desc="Crawling documents"):
            data = self.get_document_data(url)
            self.save_doc(data)

if __name__ == "__main__":
    crawler = VBPLCrawler()
    
    # Example usage for testing
    sample_url = "https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=27615"
    data = crawler.get_document_data(sample_url)
    crawler.save_doc(data)
    
    # Process the samples if they exist
    crawler.process_files("phap_dien/Dieu.json", "phap_dien/LienQuan.json")
