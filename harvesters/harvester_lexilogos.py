import os
import re
import sqlite3
import requests
import argparse
import logging
from bs4 import BeautifulSoup
from tempfile import TemporaryDirectory
from urllib.parse import urljoin

# Conditional imports for OCR pipeline
try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    HAS_OCR_DEPS = True
except ImportError:
    HAS_OCR_DEPS = False

# Configuration
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DB_NAME = "congolang_pan_congo.db"
BASE_URL = "https://www.lexilogos.com/"
PORTAL_URL = urljoin(BASE_URL, "afrique_langues.htm")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("harvester_lexilogos.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Set tesseract path
if HAS_OCR_DEPS and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def init_db():
    """Ensures the records table exists in the target database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language_code TEXT,
            region_target TEXT,
            normalized_text TEXT,
            audio_tag TEXT,
            net_votes INTEGER DEFAULT 0,
            is_honeypot BOOLEAN DEFAULT 0,
            register_type TEXT, -- FORMAL, SLANG, TECH, HERITAGE
            status TEXT DEFAULT 'UNVERIFIED'
        )
    ''')
    conn.commit()
    return conn

def normalize_historical_orthography(text):
    """
    Normalizes archaic colonial orthography into modern ILALOK standard.
    Rule 1: Double vowels -> diaeresis (aa -> ä, ee -> ë, oo -> ö)
    Rule 2: Terminal 'a' or 'i' -> apostrophe if word length > 4
    """
    if not text:
        return ""

    # Rule 1: Double vowels (Modular Regex)
    vowel_map = {'aa': 'ä', 'ee': 'ë', 'oo': 'ö'}
    for double, diaeresis in vowel_map.items():
        text = re.sub(double, diaeresis, text, flags=re.IGNORECASE)
    
    # Rule 2: Terminal truncation (a, i) for words > 4 chars
    def truncate_terminal(match):
        word = match.group(1)
        suffix = match.group(2)
        if len(word) + len(suffix) > 4:
            return word + "'"
        return word + suffix
    
    # Regex targets words ending in a or i followed by a word boundary
    text = re.sub(r'\b(\w+)([ai])\b', truncate_terminal, text, flags=re.IGNORECASE)
    
    return text

class OCRPipeline:
    def __init__(self, full_run=False):
        self.full_run = full_run
        self.max_pages = None if full_run else 5

    def extract_text_from_pdf(self, pdf_path):
        """Extracts text using Tesseract from PDF pages with graceful fallback."""
        if not HAS_OCR_DEPS:
            raise ImportError("OCR dependencies (pytesseract, pdf2image) not installed.")
        
        if not os.path.exists(TESSERACT_PATH):
            raise FileNotFoundError(f"Tesseract executable not found at {TESSERACT_PATH}")

        try:
            logging.info(f"Starting OCR on {pdf_path} (Max pages: {self.max_pages or 'All'})")
            # Set poppler_path if needed in some environments, but assuming standard installation
            images = convert_from_path(pdf_path, last_page=self.max_pages)
            full_text = ""
            for i, image in enumerate(images):
                logging.info(f"Processing page {i+1}...")
                page_text = pytesseract.image_to_string(image)
                full_text += page_text + "\n"
            return full_text
        except Exception as e:
            logging.error(f"OCR logic failed: {e}")
            raise

def scrape_lexilogos_metadata():
    """Crawl Lexilogos subpages and extract heritage resource metadata."""
    resources = []
    try:
        response = requests.get(PORTAL_URL, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target subpages from the main portal
        subpage_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            # We want Lingala and Bantu pages
            if 'lingala_dictionnaire.htm' in href or 'bantou_langues.htm' in href:
                subpage_links.append(urljoin(BASE_URL, href))
        
        # Deduplicate and crawl
        for url in set(subpage_links):
            logging.info(f"Crawling heritage metadata from: {url}")
            sub_res = requests.get(url, timeout=15)
            sub_res.raise_for_status()
            sub_soup = BeautifulSoup(sub_res.text, 'html.parser')
            
            # Heritage resources are typically in bulleted lists (•)
            for li in sub_soup.find_all(['li', 'p']):
                text = li.get_text().strip()
                if '•' in text or 'Dictionnaire' in text:
                    anchor = li.find('a', href=True)
                    if not anchor: continue
                    
                    resource_url = urljoin(url, anchor['href'])
                    title = text.replace('•', '').strip()
                    
                    # Language detection based on context
                    lang_code = 'lin' if 'lingala' in url or 'lingala' in text.lower() else 'mkw'
                    if 'vili' in text.lower() or 'fiote' in text.lower() or 'kakongo' in text.lower():
                        lang_code = 'vif'
                    
                    # Extract Year
                    year_match = re.search(r'\((\d{4})\)', text)
                    year = year_match.group(1) if year_match else "Unknown"
                    
                    resources.append({
                        'title': title,
                        'url': resource_url,
                        'lang_code': lang_code,
                        'year': year,
                        'source_text': text
                    })
                    
    except Exception as e:
        logging.error(f"Scraper encountered network error: {e}")
    
    return resources

def main():
    parser = argparse.ArgumentParser(description="CongoLang Lexilogos Heritage Harvester")
    parser.add_argument("--full-run", action="store_true", help="Process entire PDF volumes instead of sample pages")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without modifying database")
    args = parser.parse_args()

    logging.info("Initializing Lexilogos Harvester Daemon...")
    init_db()
    
    pipeline = OCRPipeline(full_run=args.full_run)
    raw_resources = scrape_lexilogos_metadata()
    
    logging.info(f"Discovered {len(raw_resources)} potential heritage resources.")

    for res in raw_resources:
        logging.info(f"Harvesting: {res['title']} ({res['lang_code']}, {res['year']})")
        
        extracted_content = ""
        status = 'UNVERIFIED'
        
        # Decide if we can OCR the resource
        is_pdf = res['url'].lower().endswith('.pdf')
        is_archive = 'archive.org' in res['url'].lower()
        
        if is_pdf and not args.dry_run:
            try:
                with TemporaryDirectory() as tmp_dir:
                    pdf_local = os.path.join(tmp_dir, "historical_volume.pdf")
                    logging.info(f"Downloading PDF stream from {res['url']}")
                    r = requests.get(res['url'], stream=True, timeout=60)
                    r.raise_for_status()
                    with open(pdf_local, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=16384):
                            f.write(chunk)
                    
                    extracted_content = pipeline.extract_text_from_pdf(pdf_local)
            except Exception as e:
                logging.warning(f"OCR Pipeline failed for {res['title']}: {e}. Falling back to metadata-only.")
                extracted_content = f"METADATA_ONLY: {res['source_text']}\nURL: {res['url']}"
                status = 'PENDING_OCR'
        else:
            # Metadata-only for web pages or archive.org (which needs complex scraping)
            extracted_content = f"SOURCE: {res['source_text']}\nURL: {res['url']}"
            status = 'PENDING_OCR'

        # Ingestion
        if not args.dry_run:
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                
                # Normalize the historical text
                normalized = normalize_historical_orthography(extracted_content)
                
                c.execute("""
                    INSERT INTO records 
                    (language_code, region_target, normalized_text, register_type, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (res['lang_code'], 'ROC_BRAZZAVILLE', normalized, 'HERITAGE', status))
                
                conn.commit()
                conn.close()
                logging.info(f"Successfully ingested {res['lang_code']} corpus record.")
            except Exception as e:
                logging.error(f"Database write failed: {e}")
        else:
            logging.info(f"DRY RUN: Would ingest {res['title']} with status {status}")

    logging.info("Harvester execution cycle complete.")

if __name__ == "__main__":
    main()
