"""
run_all.py - The Orchestrator
"""
import logging
import optimize_db
import sanitize_ui_payloads
import honeypot_service
import harvester_youtube_slang
import harvester_kituba_tech
import sqlite3

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - ORCHESTRATOR: %(message)s")

def get_total_rows():
    try:
        conn = sqlite3.connect('congolang_pan_congo.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM records")
        total = cursor.fetchone()[0]
        conn.close()
        return total
    except Exception:
        return 0

def run():
    logging.info("Starting ETL Enhancement Suite...")
    
    # 1. Optimize
    optimize_db.run()
    
    # 2. Sanitize
    sanitization_stats = sanitize_ui_payloads.run()
    excluded_length = sanitization_stats.get('length', 0)
    excluded_dupes = sanitization_stats.get('duplicates', 0)
    
    # 3. Honeypots
    seeded_honeypots = honeypot_service.run()
    
    # 4. Harvest Slang
    harvested_slang = harvester_youtube_slang.run()
    
    # 5. Harvest Tech
    harvested_tech = harvester_kituba_tech.run()
    
    total_rows = get_total_rows()
    
    # Print ASCII Summary Report
    report = f"""
=========================================================
      CONGOLANG ANTIGRAVITY ETL SUITE - FINAL REPORT      
=========================================================
Total Database Rows        : {total_rows:,}
Rows Excluded by Length    : {excluded_length:,}
Rows Excluded as Duplicate : {excluded_dupes:,}
Gold Standard Honeypots    : {seeded_honeypots:,}
New Slang Harvested        : {harvested_slang:,}
New Tech Loanwords         : {harvested_tech:,}
=========================================================
    """
    print(report)
    logging.info("ETL Enhancement Suite completed successfully.")

if __name__ == "__main__":
    run()
