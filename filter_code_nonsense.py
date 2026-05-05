import sqlite3
import re
import sys

# Configuration
DB_NAME = "congolang_pan_congo.db"
BATCH_SIZE = 1000
MAX_RETRIES = 5

# Regex Heuristics based on Senior Data Engineer specifications
# Rule 1: Explicit programming operators (single occurrence triggers exclusion)
OPERATORS_REGEX = re.compile(r'(=>|===|!==|!=|\+\+|--|//|&&|\|\||->)')

# Rule 2: Structural brackets (density >= 3 triggers exclusion)
BRACKETS_REGEX = re.compile(r'([{}\[\]])')

# Rule 3: HTML/XML Tags (detected as raw text)
TAGS_REGEX = re.compile(r'<(div|br|span|script|html|body|a|p|li|ul|ol|table|tr|td|form|input|button|style)[^>]*>', re.IGNORECASE)

# Rule 4: Keywords (Infrastructure, DevOps, Coding, Errors)
KEYWORDS_REGEX = re.compile(r'\b(git|docker|npm|sudo|apt-get|ValueError|Exception|console\.log|System\.out|public static|var|let|const|function|return;?|boolean|def|import|from|class)\b', re.IGNORECASE)

# Rule 5: Markdown Fragments
MARKDOWN_REGEX = re.compile(r'```[a-z]*', re.IGNORECASE)

def is_code_nonsense(text):
    """Evaluates if a text string contains programming syntax or technical noise."""
    if not text:
        return False
    
    # Check Rule 1: Operators (Single trigger)
    if OPERATORS_REGEX.search(text):
        return "operator_match"
        
    # Check Rule 3: HTML Tags (Single trigger)
    if TAGS_REGEX.search(text):
        return "html_tag_match"
        
    # Check Rule 4: Keywords (Single trigger)
    if KEYWORDS_REGEX.search(text):
        return "keyword_match"
        
    # Check Rule 5: Markdown (Single trigger)
    if MARKDOWN_REGEX.search(text):
        return "markdown_match"
        
    # Check Rule 2: Structural Bracket density (>= 3)
    # Using findall to count occurrences. {} or []
    # Setting threshold to 3 to allow for a single matching pair like [text] or {text}
    # while flagging technical nested structures.
    bracket_count = len(BRACKETS_REGEX.findall(text))
    if bracket_count >= 3:
        return "structural_density_match"
        
    return False

def purge_nonsense():
    """Iterates through UNVERIFIED records and tags technical noise for exclusion."""
    print(f"[*] Connecting to {DB_NAME}...")
    try:
        conn = sqlite3.connect(DB_NAME, timeout=60)
        c = conn.cursor()
    except Exception as e:
        print(f"[!] Database connection failed: {e}")
        return

    # Scan scope
    print("[*] Fetching UNVERIFIED records for scanning...")
    c.execute("SELECT id, normalized_text FROM records WHERE status = 'UNVERIFIED'")
    rows = c.fetchall()
    
    total_scanned = len(rows)
    flagged_count = 0
    ids_to_exclude = []
    
    # Statistical tracking
    reason_stats = {
        "operator_match": 0,
        "html_tag_match": 0,
        "keyword_match": 0,
        "markdown_match": 0,
        "structural_density_match": 0
    }

    print(f"[*] Scanning {total_scanned} records...")
    
    for row_id, text in rows:
        reason = is_code_nonsense(text)
        if reason:
            flagged_count += 1
            ids_to_exclude.append(row_id)
            reason_stats[reason] += 1
            
            # Batch update for performance
            if len(ids_to_exclude) >= BATCH_SIZE:
                for attempt in range(MAX_RETRIES):
                    try:
                        c.execute(f"UPDATE records SET status = 'EXCLUDED_CODE_SNIPPET' WHERE id IN ({','.join(['?']*len(ids_to_exclude))})", ids_to_exclude)
                        conn.commit()
                        break
                    except sqlite3.OperationalError as e:
                        if "locked" in str(e).lower() or "io error" in str(e).lower():
                            print(f"\n[!] DB Locked/IO Error. Retry {attempt+1}/{MAX_RETRIES}...")
                            import time
                            time.sleep(2)
                        else:
                            raise
                ids_to_exclude = []
                sys.stdout.write(f"\r[>] Flagged so far: {flagged_count}...")
                sys.stdout.flush()

    # Final batch update
    if ids_to_exclude:
        c.execute(f"UPDATE records SET status = 'EXCLUDED_CODE_SNIPPET' WHERE id IN ({','.join(['?']*len(ids_to_exclude))})", ids_to_exclude)
        conn.commit()

    print(f"\n\n[+] Scan Complete.")
    print("-" * 40)
    print(f"Total Records Scanned:   {total_scanned}")
    print(f"Total Records Flagged:   {flagged_count}")
    print(f"Active Pool Remaining:   {total_scanned - flagged_count}")
    print("-" * 40)
    print("Breakdown of Detection Heuristics:")
    for reason, count in reason_stats.items():
        percentage = (count / flagged_count * 100) if flagged_count > 0 else 0
        print(f" - {reason:25}: {count:8} ({percentage:5.1f}%)")
    print("-" * 40)
    
    conn.close()
    print("[*] Database connection closed.")

if __name__ == "__main__":
    purge_nonsense()
