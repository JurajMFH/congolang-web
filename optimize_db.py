"""
optimize_db.py - Performance & Indexing
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - optimize_db: %(message)s")
DB_PATH = 'congolang_pan_congo.db'

def run():
    logging.info("Starting database optimization...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL;")
        logging.info("WAL mode enabled.")

        # Create Compound Indexes
        indexes = [
            ("idx_records_status_hp_lang", "status, is_honeypot, language_code"),
            ("idx_records_status_lang_region", "status, language_code"), # Using language_code as region is not in schema
            ("idx_records_honeypot_lang", "is_honeypot, language_code"),
            ("idx_records_norm_text_lang", "normalized_text, language_code"),
            ("idx_records_status_textlen", "status, length(raw_text)"),
            ("idx_records_source", "source_url")
        ]

        for idx_name, cols in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON records ({cols});")
                logging.info(f"Ensured index {idx_name} on ({cols}).")
            except sqlite3.Error as e:
                logging.warning(f"Could not create index {idx_name}: {e}")

        # Execute ANALYZE
        cursor.execute("ANALYZE;")
        logging.info("ANALYZE executed successfully.")
        
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run()
