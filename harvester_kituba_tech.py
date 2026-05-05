"""
harvester_kituba_tech.py - Gap Filler (Targeted Scraping)
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - harvester_kituba_tech: %(message)s")
DB_PATH = 'congolang_pan_congo.db'
TARGET_URLS = ["https://example-tech-blog-drc.com/articles"] # Placeholder

def run():
    logging.info("Starting Kituba tech harvest...")
    keywords = ['komputa', 'kóndé', 'ladió', 'biló', 'foloni']
    harvested_count = 0
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        for url in TARGET_URLS:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                # Ignore failures for placeholders
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Broadly search text nodes
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    text_lower = text.lower()
                    
                    if any(kw in text_lower for kw in keywords):
                        cursor.execute('''
                            INSERT INTO records (source_url, language_code, raw_text, normalized_text, status, is_honeypot, register_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (url, 'mkw', text, text, 'NEW', 0, 'TECH'))
                        harvested_count += 1
                        
            except requests.RequestException:
                pass
                
        conn.commit()
        logging.info(f"Harvested {harvested_count} tech loanwords.")
        return harvested_count
        
    except Exception as e:
        logging.error(f"Error during Kituba tech harvest: {e}")
        return harvested_count
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run()
