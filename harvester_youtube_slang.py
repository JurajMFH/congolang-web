"""
harvester_youtube_slang.py - Gap Filler (Targeted Scraping)
"""
import sqlite3
import subprocess
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - harvester_youtube_slang: %(message)s")
DB_PATH = 'congolang_pan_congo.db'
TARGET_VIDEO = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Placeholder, replace with actual Congolese channel video

def run():
    logging.info("Starting YouTube slang harvest...")
    keywords = ['cooper', 'madesu', 'zando', 'indoubil', 'langila']
    harvested_count = 0
    
    try:
        # Fetch comments using yt-dlp
        # Note: --write-comments might generate a massive JSON.
        result = subprocess.run([
            "yt-dlp", 
            "--dump-json", 
            "--get-comments", 
            TARGET_VIDEO
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"yt-dlp failed: {result.stderr}")
            return 0
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
                comments = data.get('comments', [])
                
                for comment in comments:
                    text = comment.get('text', '')
                    text_lower = text.lower()
                    
                    # Count matching keywords
                    matches = sum(1 for kw in keywords if kw in text_lower)
                    
                    if matches >= 2:
                        cursor.execute('''
                            INSERT INTO records (source_url, language_code, raw_text, normalized_text, status, is_honeypot, register_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (TARGET_VIDEO, 'lin', text, text, 'NEW', 0, 'SLANG'))
                        harvested_count += 1
                        
            except json.JSONDecodeError:
                continue
                
        conn.commit()
        logging.info(f"Harvested {harvested_count} slang comments.")
        return harvested_count
        
    except Exception as e:
        logging.error(f"Error during YouTube harvest: {e}")
        return harvested_count
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    run()
