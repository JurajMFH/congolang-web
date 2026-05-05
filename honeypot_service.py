import sqlite3
import os
from datasets import load_dataset
from huggingface_hub import login

# --------------------------------------------------------------------------
# Environment & Authentication Troubleshooting
# --------------------------------------------------------------------------
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("[!] WARNING: HF_TOKEN environment variable not found in CMD.")
    print("[!] FIXED ACTION: Please run 'set HF_TOKEN=your_token' before execution.")
    HF_TOKEN = "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"

DB_NAME = "congolang_pan_congo.db"

def seed_honeypots():
    if HF_TOKEN:
        login(token=HF_TOKEN)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    print("Seeding 200 Gold Standard honeypot traps from FLORES (with trust_remote_code=True)...")
    try:
        # Added trust_remote_code=True per HF security policy
        flores = load_dataset("facebook/flores", "fra_Latn-lin_Latn", split="devtest", streaming=True, trust_remote_code=True)
        honeypots = []
        count = 0
        for item in flores:
            if count >= 200:
                break
            
            # Match the FLORES schema
            data = item.get('translation', {})
            text = data.get('lin_Latn')
            
            if text:
                honeypots.append(('lin', 'DRC_KINSHASA', text, 'FORMAL', 'STATUS_GOLD_STANDARD', 1))
                count += 1
        
        c.executemany('''
            INSERT INTO records (language_code, region_target, normalized_text, register_type, status, is_honeypot)
            VALUES (?,?,?,?,?,?)
        ''', honeypots)
        
        conn.commit()
        print(f"Successfully seeded {count} honeypots.")
    except Exception as e:
        print(f"Error seeding honeypots: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_honeypots()
