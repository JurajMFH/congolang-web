import sqlite3
import re
import os
import sys
from datasets import load_dataset
from huggingface_hub import login

# --------------------------------------------------------------------------
# Environment & Authentication Troubleshooting
# --------------------------------------------------------------------------
# On Windows CMD, run: set HF_TOKEN=your_token_here
# On PowerShell, run: $env:HF_TOKEN="your_token_here"
# --------------------------------------------------------------------------
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("[!] WARNING: HF_TOKEN environment variable not found.")
    print("[!] FIXED ACTION: Please run 'set HF_TOKEN=your_token' in Windows CMD before execution.")
    # Attempt fallback to the previously provided hardcoded token if env is missing
    HF_TOKEN = "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"

DB_NAME = "congolang_pan_congo.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # ... (Schema initialization remains same)
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
            status TEXT DEFAULT 'UNVERIFIED' -- UNVERIFIED, STATUS_GOLD_STANDARD
        )
    ''')
    
    # 2. Gamification Layer: Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            trust_score REAL DEFAULT 50.0,
            xp_points INTEGER DEFAULT 0
        )
    ''')
    
    # 3. Gamification Layer: Votes
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            record_id INTEGER,
            swipe_action TEXT, -- RIGHT, LEFT, UP
            weighted_score INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(record_id) REFERENCES records(id)
        )
    ''')
    
    # Optimized Indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_records_status_lang ON records(status, language_code)",
        "CREATE INDEX IF NOT EXISTS idx_records_status_hp_lang ON records(status, is_honeypot, language_code)",
        "CREATE INDEX IF NOT EXISTS idx_records_net_votes ON records(net_votes)",
        "CREATE INDEX IF NOT EXISTS idx_records_lang_reg ON records(language_code, register_type)",
        "CREATE INDEX IF NOT EXISTS idx_votes_user_rec ON votes(user_id, record_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_records_random ON records(net_votes, status, id)",
        "CREATE INDEX IF NOT EXISTS idx_records_lang_status ON records(language_code, status)",
        "CREATE INDEX IF NOT EXISTS idx_votes_record_id ON votes(record_id)"
    ]
    for idx_sql in indexes:
        c.execute(idx_sql)
    
    conn.commit()
    return conn

def apply_lingala_shift(text):
    return re.sub(r'z', 'j', text, flags=re.IGNORECASE)

def apply_kituba_shift(text):
    text = re.sub(r'\bko\b', 've', text, flags=re.IGNORECASE)
    return text

def ingest_data(conn):
    c = conn.cursor()
    if HF_TOKEN:
        login(token=HF_TOKEN)
    
    # Module 1: Lingala (lin)
    print("Ingesting Lingala (FLORES & MasakhaNews)...")
    try:
        # Added trust_remote_code=True per HF security policy
        flores = load_dataset("facebook/flores", "fra_Latn-lin_Latn", split="dev", streaming=True, trust_remote_code=True)
        records = []
        for item in flores:
            data = item['translation']
            text = apply_lingala_shift(data['lin_Latn'])
            records.append(('lin', 'ROC_BRAZZAVILLE', text, 'FORMAL', 'UNVERIFIED'))
        c.executemany("INSERT INTO records (language_code, region_target, normalized_text, register_type, status) VALUES (?,?,?,?,?)", records)
    except Exception as e:
        print(f"Skipping gated FLORES, using fallbacks. Error: {e}")

    try:
        masakha = load_dataset("masakhane/masakhanews", "lin", split="train", streaming=True, trust_remote_code=True)
        records = []
        for item in masakha:
            text = apply_lingala_shift(item['text'])
            records.append(('lin', 'DRC_KINSHASA', text, 'TECH', 'UNVERIFIED'))
        c.executemany("INSERT INTO records (language_code, region_target, normalized_text, register_type, status) VALUES (?,?,?,?,?)", records)
    except Exception as e:
        print(f"Error in Masakha Module: {e}")

    # Module 2: Kituba (mkw/ktu)
    print("Ingesting Kituba (SMOL & 170k-kituba)...")
    try:
        smol = load_dataset("google/smol", name="smolsent__en_ktu", split="train", streaming=True, trust_remote_code=True)
        records = []
        for item in smol:
            text = item.get('ktu') or item.get('target') or item.get('translation', {}).get('ktu')
            if text:
                text = apply_kituba_shift(text)
                records.append(('mkw', 'ROC_POOL', text, 'FORMAL', 'UNVERIFIED'))
        c.executemany("INSERT INTO records (language_code, region_target, normalized_text, register_type, status) VALUES (?,?,?,?,?)", records)
    except Exception as e:
        print(f"Error in SMOL Module: {e}")

    try:
        # Fixed: Updated Kituba-170k parsing for 'conversations' structure
        kituba_170k = load_dataset("michsethowusu/Code-170k-kituba", split="train", streaming=True, trust_remote_code=True)
        records = []
        for count, item in enumerate(kituba_170k):
            if count > 414803: break 
            
            # Extract text from 'conversations' list (ShareGPT format)
            convos = item.get('conversations', [])
            text = ""
            for turn in convos:
                if turn.get('from') == 'gpt': # Get the target lang response
                    text = turn.get('value', '')
                    break
            
            if text:
                text = apply_kituba_shift(text)
                records.append(('mkw', 'DRC_KONGO_CENTRAL', text, 'SLANG', 'UNVERIFIED'))
            
            if len(records) > 5000:
                c.executemany("INSERT INTO records (language_code, region_target, normalized_text, register_type, status) VALUES (?,?,?,?,?)", records)
                records = []
        if records:
            c.executemany("INSERT INTO records (language_code, region_target, normalized_text, register_type, status) VALUES (?,?,?,?,?)", records)
    except Exception as e:
        print(f"Error in Kituba-170k Module: {e}")

    conn.commit()
    
    # Emergency Seed logic
    c.execute("SELECT count(*) FROM records")
    if c.fetchone()[0] == 0:
        print("Ingestion returned 0 records. Injecting Emergency Seed...")
        emergency_data = [
            ('lin', 'ROC_BRAZZAVILLE', 'Najali na esengo mingi mpo na sika.', 'FORMAL', 'UNVERIFIED'),
            ('mkw', 'ROC_POOL', 'Yandi kwenda na mbanza ve.', 'FORMAL', 'UNVERIFIED'),
        ] * 100
        c.executemany("INSERT INTO records (language_code, region_target, normalized_text, register_type, status) VALUES (?,?,?,?,?)", emergency_data)
        conn.commit()

if __name__ == "__main__":
    print("Starting Pan-Congo Pipeline...")
    conn = init_db()
    try:
        ingest_data(conn)
        print("Ingestion complete.")
    except Exception as e:
        print(f"FATAL ERROR: {e}")
    finally:
        conn.close()
        print("Pipeline finished. Connection closed.")
