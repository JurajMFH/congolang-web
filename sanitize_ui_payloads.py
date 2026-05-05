"""
sanitize_ui_payloads.py - Cleaning & Deduplication
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - sanitize_ui_payloads: %(message)s")
DB_PATH = 'congolang_pan_congo.db'

def run():
    logging.info("Starting sanitization and deduplication...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Length Filter
        cursor.execute('''
            UPDATE records 
            SET status = 'EXCLUDED_BY_LENGTH' 
            WHERE (length(raw_text) < 10 OR length(raw_text) > 150)
            AND status != 'STATUS_GOLD_STANDARD';
        ''')
        length_excluded = cursor.rowcount
        logging.info(f"Excluded {length_excluded} rows by length.")

        # Deduplication
        cursor.execute('''
            UPDATE records 
            SET status = 'EXCLUDED_DUPLICATE' 
            WHERE id NOT IN (
                SELECT MIN(id) 
                FROM records 
                GROUP BY normalized_text, language_code
            )
            AND status != 'STATUS_GOLD_STANDARD'
            AND status != 'EXCLUDED_BY_LENGTH';
        ''')
        duplicates_excluded = cursor.rowcount
        logging.info(f"Excluded {duplicates_excluded} rows as duplicates.")

        conn.commit()
        return {"length": length_excluded, "duplicates": duplicates_excluded}
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return {"length": 0, "duplicates": 0}
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run()
