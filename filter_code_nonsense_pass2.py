import sqlite3
import re
import sys
import time
import argparse

# Configuration
DB_NAME = "congolang_pan_congo.db"
BATCH_SIZE = 1000
MAX_RETRIES = 5

# Regex Heuristics for Pass 2 (New edge cases)
# Rule 1: Inline Code & Backticks
BACKTICK_REGEX = re.compile(r'`')

# Rule 2: Markdown Links & Bold
MD_LINKS_REGEX = re.compile(r'\[.*?\]\(.*?\)')
MD_BOLD_REGEX = re.compile(r'\*\*.*?\*\*')

# Rule 3: Mentions & Usernames (e.g., @github_user)
MENTIONS_REGEX = re.compile(r'@\w+')

# Rule 4: Snake_Case Variables (Only letters connecting with underscores)
SNAKE_CASE_REGEX = re.compile(r'\b[a-zA-Z]+_[a-zA-Z]+\b')

# Rule 5: Paths & Deep Directories (Deep slash structures or date-like paths)
PATHS_REGEX = re.compile(r'\b\w*(?:/\w+){2,}\b')

# Rule 6: Additional Tech Keywords
KEYWORDS_REGEX = re.compile(r'\b(plugin)\b', re.IGNORECASE)

def is_code_noise_pass2(text):
    """Detects new edge cases for programming noise in the textual content."""
    if not text:
        return False
    
    if BACKTICK_REGEX.search(text): return "backtick_match"
    if MD_LINKS_REGEX.search(text): return "md_link_match"
    if MD_BOLD_REGEX.search(text): return "md_bold_match"
    if MENTIONS_REGEX.search(text): return "mention_match"
    if SNAKE_CASE_REGEX.search(text): return "snake_case_match"
    if PATHS_REGEX.search(text): return "path_match"
    if KEYWORDS_REGEX.search(text): return "keyword_match"
    
    return False

def hard_delete_nonsense():
    """Performs Pass 1 cleanup and Pass 2 HARD DELETE of programming nonsense."""
    parser = argparse.ArgumentParser(description="CongoLang Code Nonsense Hard Delete (Pass 2)")
    parser.add_argument("--dry-run", action="store_true", help="Count records to be deleted without performing hard delete")
    args = parser.parse_args()

    print(f"[*] Initializing Hard Delete Pass 2 on {DB_NAME}...")
    if args.dry_run:
        print("[!] DRY RUN MODE ENABLED. No records will be deleted.")
    
    try:
        conn = sqlite3.connect(DB_NAME, timeout=60)
        c = conn.cursor()
    except Exception as e:
        print(f"[!] Database connection failed: {e}")
        return

    # Pass 1 Cleanup
    print("[*] Pass 1 Cleanup: Deleting records with status = 'EXCLUDED_CODE_SNIPPET'...")
    c.execute("SELECT COUNT(*) FROM records WHERE status = 'EXCLUDED_CODE_SNIPPET'")
    pass1_count = c.fetchone()[0]
    
    if pass1_count > 0:
        if not args.dry_run:
            for attempt in range(MAX_RETRIES):
                try:
                    c.execute("DELETE FROM records WHERE status = 'EXCLUDED_CODE_SNIPPET'")
                    conn.commit()
                    print(f"[+] Purged {pass1_count} records from previous Pass 1.")
                    break
                except sqlite3.OperationalError:
                    print(f"[!] DB Locked. Retrying Pass 1 purge ({attempt+1}/{MAX_RETRIES})...")
                    time.sleep(2)
        else:
            print(f"[DRY RUN] Would purge {pass1_count} records from Pass 1.")
    else:
        print("[!] No records found with status 'EXCLUDED_CODE_SNIPPET'.")

    # Pass 2 Identify & Delete
    print("[*] Pass 2 Filtering: Scanning UNVERIFIED records for new noise heuristics...")
    c.execute("SELECT id, normalized_text FROM records WHERE status = 'UNVERIFIED'")
    rows = c.fetchall()
    
    total_scanned = len(rows)
    pass2_deleted_count = 0
    ids_to_delete = []
    reason_stats = {}
    
    print(f"[*] Scanning {total_scanned} active records...")
    
    for row_id, text in rows:
        reason = is_code_noise_pass2(text)
        if reason:
            pass2_deleted_count += 1
            ids_to_delete.append(row_id)
            reason_stats[reason] = reason_stats.get(reason, 0) + 1
            
            if len(ids_to_delete) >= BATCH_SIZE and not args.dry_run:
                for attempt in range(MAX_RETRIES):
                    try:
                        c.execute(f"DELETE FROM records WHERE id IN ({','.join(['?']*len(ids_to_delete))})", ids_to_delete)
                        conn.commit()
                        break
                    except sqlite3.OperationalError:
                        time.sleep(2)
                ids_to_delete = []
                sys.stdout.write(f"\r[>] HARD DELETED: {pass2_deleted_count} (Pass 2)...")
                sys.stdout.flush()

    if ids_to_delete and not args.dry_run:
        c.execute(f"DELETE FROM records WHERE id IN ({','.join(['?']*len(ids_to_delete))})", ids_to_delete)
        conn.commit()

    print(f"\n\n[+] Scan {'(DRY RUN)' if args.dry_run else ''} Complete.")
    print("-" * 50)
    print(f"Pass 1 Records Permanently Purged: {pass1_count:8}")
    print(f"Pass 2 Records Permanently Purged: {pass2_deleted_count:8}")
    print(f"TOTAL ROWS REMOVED FROM DATABASE:  {pass1_count + pass2_deleted_count:8}")
    print("-" * 50)
    print("Pass 2 Detection Breakdown:")
    for reason, count in sorted(reason_stats.items(), key=lambda x: x[1], reverse=True):
        print(f" - {reason:25}: {count:8}")
    print("-" * 50)
    
    if not args.dry_run:
        print("[*] Reclaiming disk space (VACUUM)...")
        try:
            conn.execute("VACUUM")
            print("[+] Disk space reclaimed.")
        except Exception as e:
            print(f"[!] Vacuum failed: {e}")
        
    conn.close()

if __name__ == "__main__":
    hard_delete_nonsense()
