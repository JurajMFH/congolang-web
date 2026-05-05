"""
CongoLang Autonomous Data Acquisition and Processing Pipeline

Role: Senior Data Engineer & Computational Linguist
Objective: Modular, headless Python script for "offline-first" data acquisition 
using SQLite3, designed for low-bandwidth environments in the Republic of the Congo.

Dependencies: requests, beautifulsoup4, pandas, sqlite3
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import logging
from datetime import datetime

# ==========================================
# Logging Configuration
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler("congolang_pipeline.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

DB_PATH = 'congolang_offline.db'

# ==========================================
# Database Initialization (SQLite Offline-First)
# ==========================================
def init_db():
    """
    Initializes the offline-first SQLite database and creates the corpus table.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create corpus table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corpus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT,
                language_code TEXT,
                raw_text TEXT,
                normalized_text TEXT,
                dialect_flag TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()
        logging.info(f"Database initialized successfully at {DB_PATH}.")
    except sqlite3.Error as e:
        logging.error(f"SQLite initialization error: {e}")
    finally:
        if conn:
            conn.close()

def insert_raw_corpus(url, lang_code, raw_text):
    """
    Inserts the raw harvested text into the SQLite corpus table.
    Returns the inserted record's ID.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO corpus (source_url, language_code, raw_text, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (url, lang_code, raw_text, timestamp))
        
        record_id = cursor.lastrowid
        conn.commit()
        logging.info(f"Inserted raw text from {url} into DB with ID: {record_id}")
        return record_id
    except sqlite3.Error as e:
        logging.error(f"SQLite insertion error for URL {url}: {e}")
        return None
    finally:
        if conn:
            conn.close()

# ==========================================
# Module 1: Targeted Harvester (Scraping)
# ==========================================
def harvest_jw(url, lang_code):
    """
    Scrapes parallel article text from JW.org.
    Strips scripts, styles, headers, and footers.
    Inserts raw text into the SQLite database.
    """
    logging.info(f"Starting harvest for URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CongoLangPipeline/1.0'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strip unwanted tags
        for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
            element.extract()
            
        # Target JW.org article body text (often inside article or specific div classes)
        # Using a broad approach targeting main content areas commonly found
        article_body = soup.find('article')
        if not article_body:
            # Fallback for generic structure
            article_body = soup.find('div', id='article') or soup.find('div', class_='body-txt')
            
        if not article_body:
            logging.warning(f"Could not find main article body on {url}. Harvesting entire cleaned body.")
            article_body = soup.body
            
        raw_text = article_body.get_text(separator='\n', strip=True) if article_body else ""
        
        if raw_text:
            logging.info(f"Successfully scraped {len(raw_text)} characters from {url}")
            # Insert immediately upon retrieval for offline persistence
            insert_raw_corpus(url, lang_code, raw_text)
        else:
            logging.warning(f"No text extracted from {url}")
            
    except requests.RequestException as e:
        logging.error(f"Network error while harvesting {url}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error harvesting {url}: {e}")
        
    # Polite scraping delay
    delay = 3
    logging.info(f"Sleeping for {delay} seconds to respect server limits...")
    time.sleep(delay)

# ==========================================
# Module 2: Linguistic Normalizer
# ==========================================
def normalize_vili_orthography(text):
    """
    Converts historical 1902 Marichelle Vili text to modern 2008 ILALOK standard.
    - aa -> ä, ee -> ë, oo -> ö
    - Truncates specific terminal vowels and replaces with an apostrophe (e.g. mwana -> mwän')
    """
    if not text:
        return text
        
    # 1. Replace doubled vowels with diaeresis
    text = re.sub(r'aa', 'ä', text, flags=re.IGNORECASE)
    text = re.sub(r'ee', 'ë', text, flags=re.IGNORECASE)
    text = re.sub(r'oo', 'ö', text, flags=re.IGNORECASE)
    
    # 2. Truncate specific terminal vowels following specific consonants (e.g. mwana -> mwän')
    # Assuming standard Bantu noun class prefixes/roots where terminal 'a' drops
    # This regex specifically handles the 'mwana' to 'mwän'' example as requested.
    # It can be expanded based on rigorous linguistic rules.
    text = re.sub(r'\b([Mm]w[äa]n)a\b', r"\1'", text)
    
    # Generic rule: words ending in 'na', 'ma' might drop terminal 'a' in some dialects
    # text = re.sub(r'([nm])a\b', r"\1'", text) # Example of a broader rule
    
    return text

# ==========================================
# Module 3: Heuristic Verification (Dialect Disambiguation)
# ==========================================
def verify_kituba_mkw(text):
    """
    Performs character/word n-gram checks to differentiate Munukutuba (mkw) 
    from ethnic Kikongo or DRC Kikongo ya Leta (ktu).
    Returns a dialect flag string.
    """
    if not text:
        return 'UNKNOWN'
        
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    # Frequencies
    ko_count = words.count('ko')
    ve_count = words.count('ve')
    
    # Kituba pronouns and markers
    kituba_pronouns = ['munu', 'nge', 'yandi', 'beto', 'beno', 'bau']
    verb_markers = ['ke', 'kele']
    
    pronoun_count = sum(words.count(p) for p in kituba_pronouns)
    marker_count = sum(words.count(m) for m in verb_markers)
    
    total_words = len(words)
    if total_words == 0:
        return 'UNKNOWN'
        
    # Logic 1: Ethnic Kikongo flag (high 'ko' negative marker usage)
    if ko_count > ve_count * 2 and ko_count > 0:
        return 'FLAG_KIKONGO'
        
    # Logic 2: Ensure presence of isolating Kituba syntax (pronouns + markers)
    # If a text is long enough but lacks standard Kituba markers, flag it.
    if total_words > 50 and (pronoun_count == 0 or marker_count == 0):
        # Could be pure Kikongo or a heavily frenchified variant
        return 'FLAG_KTU'
        
    # Default to valid
    return 'VALID_MKW'

# ==========================================
# Module 4: Export for Orange3 QA
# ==========================================
def export_to_orange_csv():
    """
    Reads the SQLite corpus table and exports a clean CSV.
    Filters out any rows where dialect_flag contains the word 'FLAG'.
    """
    export_filename = 'congo_corpus_qa.csv'
    logging.info(f"Starting export to {export_filename}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Read the entire table using pandas
        df = pd.read_sql_query("SELECT * FROM corpus", conn)
        
        if df.empty:
            logging.warning("Corpus table is empty. Nothing to export.")
            return
            
        # Filter out rows where dialect_flag contains 'FLAG'
        # Handle NaN values gracefully
        initial_count = len(df)
        clean_df = df[~df['dialect_flag'].astype(str).str.contains('FLAG', na=False)]
        filtered_count = initial_count - len(clean_df)
        
        # Export to CSV
        clean_df.to_csv(export_filename, index=False, encoding='utf-8')
        logging.info(f"Export successful. Saved {len(clean_df)} rows to {export_filename}. Filtered out {filtered_count} flagged rows.")
        
    except Exception as e:
        logging.error(f"Error during CSV export: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# ==========================================
# Processing Pipeline Execution
# ==========================================
def run_processing_pipeline():
    """
    Iterates over the database to apply normalizations and dialect verification.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, raw_text, language_code FROM corpus WHERE normalized_text IS NULL OR dialect_flag IS NULL")
        records = cursor.fetchall()
        
        for record_id, raw_text, lang_code in records:
            normalized = raw_text
            flag = 'UNVERIFIED'
            
            # Apply normalizations based on language
            if lang_code == 'vif':
                normalized = normalize_vili_orthography(raw_text)
                flag = 'VALID_VILI' # Simple default for Vili
            elif lang_code == 'mkw':
                flag = verify_kituba_mkw(raw_text)
                
            # Update DB
            cursor.execute('''
                UPDATE corpus 
                SET normalized_text = ?, dialect_flag = ? 
                WHERE id = ?
            ''', (normalized, flag, record_id))
            
        conn.commit()
        logging.info(f"Processed and updated {len(records)} records in the database.")
        
    except sqlite3.Error as e:
        logging.error(f"Database error during processing: {e}")
    finally:
        if conn:
            conn.close()

# ==========================================
# Main Execution Block
# ==========================================
if __name__ == "__main__":
    logging.info("Starting CongoLang Pipeline Daemon...")
    init_db()
    
    # Example Usage (Uncomment to test):
    # harvest_jw("https://wol.jw.org/en/wol/d/r1/lp-e/1102014260", "mkw")
    # run_processing_pipeline()
    # export_to_orange_csv()
    
    logging.info("Pipeline execution finished.")

