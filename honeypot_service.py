"""
honeypot_service.py - Gold Standard Seeding
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - honeypot_service: %(message)s")
DB_PATH = 'congolang_pan_congo.db'

def seed_honeypots(conn, n=200):
    cursor = conn.cursor()
    total_seeded = 0
    languages = ['lin', 'mkw', 'swc', 'lua']
    
    for lang in languages:
        # Select n records per language from the target source
        cursor.execute('''
            SELECT id FROM records
            WHERE language_code = ? 
            AND source_url LIKE '%openlanguagedata/flores_plus%'
            AND status != 'STATUS_GOLD_STANDARD'
            LIMIT ?
        ''', (lang, n))
        
        records = cursor.fetchall()
        
        if not records:
            logging.warning(f"No flores_plus records found for language {lang}")
            continue
            
        record_ids = [r[0] for r in records]
        
        cursor.execute(f'''
            UPDATE records
            SET is_honeypot = 1, status = 'STATUS_GOLD_STANDARD'
            WHERE id IN ({','.join(['?']*len(record_ids))})
        ''', record_ids)
        
        seeded = cursor.rowcount
        total_seeded += seeded
        logging.info(f"Seeded {seeded} honeypots for {lang}.")
        
    conn.commit()
    return total_seeded

def run():
    logging.info("Starting honeypot seeding...")
    try:
        conn = sqlite3.connect(DB_PATH)
        seeded_count = seed_honeypots(conn, n=200)
        logging.info(f"Total honeypots seeded: {seeded_count}")
        return seeded_count
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return 0
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run()
