import sqlite3

DB_NAME = "congolang_pan_congo.db"
TARGET_ROWS = 246427

def sanitize():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Remove duplicates and filter by length
    print("Sanitizing payloads (Filtering 10-150 chars, removing duplicates)...")
    c.execute('''
        DELETE FROM records 
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM records
            WHERE length(normalized_text) BETWEEN 10 AND 150
            GROUP BY normalized_text, language_code
        )
    ''')
    
    # 2. Check current count
    c.execute("SELECT COUNT(*) FROM records")
    count = c.fetchone()[0]
    print(f"Current count after basic sanitization: {count}")
    
    # 3. Truncate to exact target if requested (to match gamification pool spec)
    if count > TARGET_ROWS:
        print(f"Truncating to exact target: {TARGET_ROWS}")
        c.execute(f"DELETE FROM records WHERE id NOT IN (SELECT id FROM records ORDER BY id LIMIT {TARGET_ROWS})")
    
    conn.commit()
    c.execute("SELECT COUNT(*) FROM records")
    final_count = c.fetchone()[0]
    print(f"Final Gamification Pool size: {final_count}")
    conn.close()

if __name__ == "__main__":
    sanitize()
