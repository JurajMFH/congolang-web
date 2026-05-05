import sqlite3
import logging
import pandas as pd
from datasets import load_dataset
import re

# Configure logging
logging.basicConfig(
    filename='global_translations.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = 'congolang_pan_congo.db'

def init_db(db_path):
    """Initializes the database schema for global translations."""
    logging.info(f"Initializing database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create the global_translations table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS global_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sentence_id INTEGER,
            congo_lang_code TEXT,
            congo_text TEXT,
            eng_text TEXT,
            fra_text TEXT,
            slk_text TEXT,
            rus_text TEXT,
            zho_text TEXT,
            status TEXT DEFAULT 'STATUS_GOLD_STANDARD',
            UNIQUE(sentence_id, congo_lang_code)
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database initialization complete. Table 'global_translations' is ready.")

def verify_kituba(text):
    """
    Applies heuristic N-gram rules to distinguish Kituba from Kikongo.
    Standard Kikongo uses 'ko' as a negative marker.
    Kituba typically uses the isolating marker 've'.
    Returns True if it appears to be Kituba, False if it appears to be Kikongo.
    """
    # Simple word boundary regex to check for exact word matches
    words = set(re.findall(r'\b\w+\b', text.lower()))
    
    if 'ko' in words and 've' not in words:
        return False  # Penalize "ko" without "ve"
    return True # Favor standard Kituba isolating markers or default to True

def align_global_sentences():
    """
    Connects to Hugging Face FLORES+ and fetches translations.
    Aligns African base languages with 5 global targets.
    """
    logging.info("Starting FLORES+ harvester and aligner...")
    
    base_langs = ['lin_Latn', 'tsh_Latn', 'swc_Latn', 'ktu_Latn']
    target_langs = {
        'eng_text': 'eng_Latn',
        'fra_text': 'fra_Latn',
        'slk_text': 'slk_Latn',
        'rus_text': 'rus_Cyrl',
        'zho_text': 'zho_Hans'
    }
    splits = ['dev', 'devtest']
    
    dataset_cache = {}
    
    # Helper to load dataset safely
    def get_split(lang_code, split_name):
        key = f"{lang_code}_{split_name}"
        if key not in dataset_cache:
            try:
                logging.info(f"Downloading FLORES+ split '{split_name}' for language '{lang_code}'...")
                # FLORES+ requires trust_remote_code=True for custom loading scripts
                dataset_cache[key] = load_dataset("openlanguagedata/flores_plus", lang_code, split=split_name, trust_remote_code=True)
            except Exception as e:
                logging.error(f"Failed to load FLORES+ dataset for {lang_code} ({split_name}): {e}")
                return None
        return dataset_cache[key]

    aligned_records = []
    
    for split in splits:
        # Pre-load targets by id
        targets_by_id = {}
        for target_key, target_code in target_langs.items():
            ds = get_split(target_code, split)
            if ds is None:
                continue
            targets_by_id[target_key] = {row['id']: row['sentence'] for row in ds}
            
        # Process base languages
        for base_code in base_langs:
            base_ds = get_split(base_code, split)
            if base_ds is None:
                continue
            
            for row in base_ds:
                sentence_id = row['id']
                congo_text = row['sentence']
                
                # Verify dialect if Kituba
                status = 'STATUS_GOLD_STANDARD'
                if base_code == 'ktu_Latn':
                    if not verify_kituba(congo_text):
                        status = 'STATUS_FLAGGED_KTU'
                        logging.debug(f"Flagged Kituba sentence {sentence_id}: {congo_text}")
                
                # Build the record
                record = {
                    'sentence_id': sentence_id,
                    'congo_lang_code': base_code,
                    'congo_text': congo_text,
                    'status': status
                }
                
                # Fill in global translations
                for target_key in target_langs.keys():
                    record[target_key] = targets_by_id.get(target_key, {}).get(sentence_id, None)
                    
                aligned_records.append(record)
                
    logging.info(f"Successfully aligned {len(aligned_records)} total cross-lingual sentence pairs.")
    return aligned_records

def ingest_aligned_data(db_path, aligned_records):
    """
    Safely bulk inserts aligned records into SQLite using INSERT OR IGNORE.
    """
    if not aligned_records:
        logging.warning("No records to ingest. Skipping ingestion.")
        return
        
    logging.info(f"Ingesting {len(aligned_records)} records into {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    insert_sql = '''
        INSERT OR IGNORE INTO global_translations (
            sentence_id, congo_lang_code, congo_text, 
            eng_text, fra_text, slk_text, rus_text, zho_text, status
        ) VALUES (
            :sentence_id, :congo_lang_code, :congo_text,
            :eng_text, :fra_text, :slk_text, :rus_text, :zho_text, :status
        )
    '''
    
    try:
        cursor.executemany(insert_sql, aligned_records)
        inserted_count = cursor.rowcount
        conn.commit()
        logging.info(f"Successfully ingested {inserted_count} new records (ignoring duplicates).")
    except Exception as e:
        logging.error(f"Error during bulk ingestion: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    logging.info("--- Starting module_global_translations.py ---")
    try:
        init_db(DB_PATH)
        aligned_data = align_global_sentences()
        ingest_aligned_data(DB_PATH, aligned_data)
        logging.info("--- module_global_translations.py completed successfully ---")
    except Exception as e:
        logging.error(f"Critical failure in global translations pipeline: {e}", exc_info=True)
