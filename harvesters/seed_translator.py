# -*- coding: utf-8 -*-
import os
import time
import sqlite3
import sys

# Ensure we can import gemini_service from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from gemini_service import translate_term
except ImportError:
    # Fallback for different working directory scenarios
    sys.path.append(".")
    from gemini_service import translate_term

# Configuration
DB_NAME = "congolang_pan_congo.db"
REGION_TARGET = 'ROC_BRAZZAVILLE'

# Target Languages Matrix
TARGET_LANGUAGES = {
    'lin': 'Lingala',
    'mkw': 'Munukutuba/Kituba',
    'ldi': 'Lari',
    'vif': 'Vili',
    'mdw': 'Mbochi',
    'eng': 'English',
    'slk': 'Slovak'
}

# Seed Dictionary (French)
NUMBERS = [u'Zéro', u'Un', u'Deux', u'Trois', u'Quatre', u'Cinq', u'Six', u'Sept', u'Huit', u'Neuf', u'Dix', u'Cent', u'Mille']
MONTHS = [u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin', u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre', u'Décembre']

def run_harvester():
    # Detect database location
    db_path = DB_NAME
    if not os.path.exists(db_path):
        db_path = os.path.join("..", DB_NAME)
    
    if not os.path.exists(db_path):
        print(f"[-] Error: Could not find database at {DB_NAME} or {db_path}")
        return

    print(f"[+] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    all_terms = NUMBERS + MONTHS
    success_count = 0
    error_count = 0
    
    print(f"[+] Starting seed translation harvester for {len(all_terms)} terms across {len(TARGET_LANGUAGES)} languages.")
    print(f"[+] Matrix: 23 terms * 7 languages = 161 total expected records.")
    print("-" * 60)
    
    for term in all_terms:
        for lang_code, lang_name in TARGET_LANGUAGES.items():
            print(f"[*] Translating: [{term}] to {lang_name}...")
            
            # API Call via gemini_service
            translation = translate_term(term, lang_name)
            
            if translation:
                # Requirement: [French] -> [Translation] format
                normalized_text = f"{term} -> {translation}"
                
                try:
                    cursor.execute('''
                        INSERT INTO records (language_code, region_target, normalized_text, register_type, is_honeypot, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (lang_code, REGION_TARGET, normalized_text, 'FORMAL', 0, 'UNVERIFIED'))
                    print(f"    [OK] Ingested: {normalized_text}")
                    success_count += 1
                except Exception as e:
                    print(f"    [!] DB Error: {e}")
                    error_count += 1
            else:
                print(f"    [!] Translation FAILED for '{term}' to {lang_name}")
                error_count += 1
            
            # Rate limit handling: 2 seconds between API calls as requested
            time.sleep(2)
            
    conn.commit()
    conn.close()
    
    print("-" * 60)
    print(f"[+] Harvester execution complete.")
    print(f"[+] Total Success: {success_count}")
    print(f"[+] Total Errors: {error_count}")

if __name__ == "__main__":
    run_harvester()
