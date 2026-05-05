import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import sys

# ==============================================================================
# Database Configuration & Schema Definition
# ==============================================================================

DB_NAME = "congolang_lessons_core.db"

def init_db():
    """
    Initializes the SQLite database with the heavily commented schema.
    This database is strictly local and highly portable as a single .db file.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # --------------------------------------------------------------------------
    # TABLE: lexilogos_raw_corpus
    # --------------------------------------------------------------------------
    # This table serves as the "Dump / Staging Area". It holds unfiltered, 
    # unprocessed text exactly as it was pulled from external sources.
    # 
    # Columns:
    # id: Unique identifier for each scraped entry.
    # french_original: The French text retrieved.
    # lingala_translation: The corresponding Lingala text.
    # source: Where the data came from (e.g., the specific URL).
    # notes: Any anomalies detected during the scrape (e.g., HTML structure variations).
    # --------------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lexilogos_raw_corpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            french_original TEXT NOT NULL,
            lingala_translation TEXT NOT NULL,
            source TEXT,
            notes TEXT
        )
    ''')


    # --------------------------------------------------------------------------
    # TABLE: lingohut_lessons
    # --------------------------------------------------------------------------
    # Based on Lingohut's pedagogical architecture: topics are divided into 
    # manageable 5-minute chunks targeting practical/survival scenarios.
    #
    # Columns:
    # lesson_id: Unique lesson identifier.
    # topic_name: The descriptive name of the lesson (e.g., "Lesson 1: Greetings").
    # difficulty: integer representing the learning curve (1=Beginner, 2=Intermediate).
    # --------------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lingohut_lessons (
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT UNIQUE NOT NULL,
            difficulty INTEGER DEFAULT 1
        )
    ''')

    # Pre-populate specific lessons defined in the pedagogical mapping rules.
    topics = [
        ("Lesson 1: Basic Greetings", 1),
        ("Lesson 2: Numbers", 1),
        ("Lesson 3: Family", 1),
        ("Lesson 4: Food & Drink", 1),
        ("Lesson 5: Survival & Verbs", 2),
        ("Lesson 6: General Vocabulary", 2)
    ]
    cursor.executemany('''
        INSERT OR IGNORE INTO lingohut_lessons (topic_name, difficulty)
        VALUES (?, ?)
    ''', topics)


    # --------------------------------------------------------------------------
    # TABLE: lingohut_flashcards
    # --------------------------------------------------------------------------
    # This table formats data strictly for flashcard review (Lingohut style),
    # creating the mapping between the lesson topic and the vocabulary pair.
    #
    # Columns:
    # card_id: Unique identifier for the flashcard.
    # lesson_id: Foreign key linking back to the lingohut_lessons table.
    # word_stem: An identifying root or clean keyword (used to cluster similar words).
    # french: Cleaned French display text.
    # lingala: Cleaned Lingala display text (with dialect rules applied).
    # audio_tag: Placeholder for linking a future voice audio file (e.g., 'hello_lin.mp3').
    # --------------------------------------------------------------------------
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lingohut_flashcards (
            card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            word_stem TEXT,
            french TEXT NOT NULL,
            lingala TEXT NOT NULL,
            audio_tag TEXT,
            FOREIGN KEY (lesson_id) REFERENCES lingohut_lessons(lesson_id)
        )
    ''')

    conn.commit()
    return conn


# ==============================================================================
# Step 1: Lexilogos Deep Scraping
# ==============================================================================

def scrape_lexilogos(conn):
    """
    Downloads and parses available parallel content from Lexilogos.
    Because the Lexilogos index doesn't have a rigid dictionary table inherently,
    we look for specific textual artifacts, list items, or paragraphs that contain bilingual splits.
    
    Includes robust try/except networking blocks and a fallback payload 
    to ensure the pipeline never fails on varied or inaccessible DOM structures.
    """
    url = "https://www.lexilogos.com/lingala_dictionnaire.htm"
    cursor = conn.cursor()
    scraped_pairs = []
    
    print(f"[*] Attempting to deep scrape {url}...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Heuristic search: look for lines that contain hyphens or colons as dividers
        # within list items or specific divs. (This is a generic approach since there is no standard table).
        for element in soup.find_all(['li', 'p']):
            text = element.get_text(separator=' ', strip=True)
            if ' - ' in text:
                parts = text.split(' - ', 1)
                if len(parts) == 2 and len(parts[0]) < 50 and len(parts[1]) < 100:
                    scraped_pairs.append({
                        "fr": parts[0].strip(),
                        "lin": parts[1].strip(),
                        "source": url,
                        "notes": "Parsed from deep markup separator"
                    })
            elif ' : ' in text: # specific non-breaking space colon used in lexilogos
                parts = text.split(' : ', 1)
                if len(parts) == 2 and len(parts[0]) < 50 and len(parts[1]) < 100:
                     scraped_pairs.append({
                        "fr": parts[1].strip(),
                        "lin": parts[0].strip(),
                        "source": url,
                        "notes": "Parsed from list item"
                    })

    except requests.RequestException as e:
        print(f"[-] Network/Scraping error: {e}")
    except Exception as e:
        print(f"[-] Parsing error: {e}")

    # Fallback / Seed Data payload
    # Web scraping external directory indices often yields low parallel pairs directly in the HTML.
    # To demonstrate the Lingohut pedagogical mapper and dialect shifts robustly, we inject foundational survival data.
    if len(scraped_pairs) < 5:
        print("[!] Scraping yielded minimal direct dictionary tables. Injecting robust survival core dataset...")
        seed_data = [
            ("bonjour", "mbote"), ("merci", "melesi"), ("oui", "ee"), ("non", "te"),
            ("un", "moko"), ("deux", "mibale"), ("trois", "misato"), ("quatre", "minei"),
            ("père", "tata"), ("mère", "mama"), ("frère/soeur", "ndeko"), ("enfant", "mwana"),
            ("eau", "mai"), ("pain", "mampa"), ("nourriture", "bilei"),
            ("je m'appelle", "kombo na ngai"), ("je suis", "nazali"), ("je veux", "nalingi"), ("au revoir", "kenda malamu")
        ]
        for fr, lin in seed_data:
            scraped_pairs.append({"fr": fr, "lin": lin, "source": "Core Seed Database", "notes": "Seed"})

    # Insert into raw staging db
    for pair in scraped_pairs:
        # Avoid exact duplicates in the raw corpus
        cursor.execute("SELECT id FROM lexilogos_raw_corpus WHERE french_original=? AND lingala_translation=?", (pair['fr'], pair['lin']))
        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO lexilogos_raw_corpus (french_original, lingala_translation, source, notes)
                VALUES (?, ?, ?, ?)
            ''', (pair['fr'], pair['lin'], pair['source'], pair['notes']))
    
    conn.commit()
    print(f"[+] Total raw pairs available in corpus: {len(scraped_pairs)}")


# ==============================================================================
# Step 2: Lingohut Pedagogical Architecture & Mapper
# ==============================================================================

def apply_brazzaville_dialect(lingala_text):
    """
    Applies heuristics specific to Congolese Lingala (Brazzaville).
    A common phonetic shift in Brazzaville is the 'z' turning into a 'j'.
    For example: "nazali" (I am) -> "najali". "zoba" (fool) -> "joba".
    """
    # Simple replace for demonstration. 
    # In a full production linguistic model, you would avoid words where 'z' shouldn't change,
    # or rely on regex word boundaries \b.
    modified_text = re.sub(r'(?i)z', 'j', lingala_text)
    return modified_text

def map_raw_to_lingohut(conn):
    """
    The "Gap Filler / Mapper".
    Extracts raw lexilogos corpus data, identifies topics based on keywords,
    applies phonetic shifts, and structures the data into the flashcard schema.
    """
    cursor = conn.cursor()
    
    # Retrieve all topic IDs for mapping
    cursor.execute("SELECT lesson_id, topic_name FROM lingohut_lessons")
    lessons = {name: l_id for l_id, name in cursor.fetchall()}
    
    # Keyword associations for Lingohut heuristic sorting
    topic_heuristics = {
        "Lesson 1: Basic Greetings": ["bonjour", "mbote", "merci", "melesi", "au revoir", "salut", "kombo"],
        "Lesson 2: Numbers": ["un", "deux", "trois", "quatre", "cinq", "moko", "mibale", "misato"],
        "Lesson 3: Family": ["père", "mère", "tata", "mama", "frère", "soeur", "ndeko", "mwana"],
        "Lesson 4: Food & Drink": ["eau", "pain", "mai", "mampa", "nourriture", "boire", "manger", "bilei"],
        "Lesson 5: Survival & Verbs": ["suis", "veux", "nazali", "nalingi", "oui", "non", "ee", "te"]
    }

    cursor.execute("SELECT id, french_original, lingala_translation FROM lexilogos_raw_corpus")
    raw_data = cursor.fetchall()
    
    for row in raw_data:
        record_id, fr, lin = row
        fr_lower, lin_lower = fr.lower(), lin.lower()
        
        # Determine target lesson
        target_lesson_name = "Lesson 6: General Vocabulary" # default fallback
        
        for topic, keywords in topic_heuristics.items():
            if any(kw in fr_lower or kw in lin_lower for kw in keywords):
                target_lesson_name = topic
                break
                
        lesson_id = lessons[target_lesson_name]
        
        # Apply Brazzaville heuristic (z -> j)
        brazza_lingala = apply_brazzaville_dialect(lin)
        
        word_stem = fr_lower.split()[0] if fr_lower else "unknown"
        audio_tag = f"{word_stem}_{lesson_id}.mp3"
        
        # Insert into pedagogical flashcard structure
        cursor.execute("SELECT card_id FROM lingohut_flashcards WHERE french=? AND lingala=?", (fr, brazza_lingala))
        if cursor.fetchone() is None:
            cursor.execute('''
                INSERT INTO lingohut_flashcards (lesson_id, word_stem, french, lingala, audio_tag)
                VALUES (?, ?, ?, ?, ?)
            ''', (lesson_id, word_stem, fr, brazza_lingala, audio_tag))

    conn.commit()


# ==============================================================================
# Step 3: Summary and Output Statistics
# ==============================================================================

def print_db_summary(conn):
    """
    Outputs statistics upon completion of the script pipeline.
    """
    cursor = conn.cursor()
    print("\n" + "="*50)
    print(" PIPELINE COMPLETION SUMMARY ")
    print("="*50)
    
    cursor.execute("SELECT COUNT(*) FROM lexilogos_raw_corpus")
    raw_count = cursor.fetchone()[0]
    print(f"[*] Total words/phrases in scraped raw corpus: {raw_count}")
    
    cursor.execute("SELECT COUNT(*) FROM lingohut_flashcards")
    flashcard_count = cursor.fetchone()[0]
    print(f"[*] Total flashcards successfully mapped: {flashcard_count}")
    
    print("\n[*] Breakdown by Lingohut Lesson Mapping:")
    cursor.execute('''
        SELECT ll.topic_name, COUNT(lf.card_id) 
        FROM lingohut_lessons ll
        LEFT JOIN lingohut_flashcards lf ON ll.lesson_id = lf.lesson_id
        GROUP BY ll.lesson_id
        ORDER BY ll.lesson_id ASC
    ''')
    for topic, count in cursor.fetchall():
         print(f"    - {topic}: {count} flashcards")
         
    # Show a few sample transformations (z -> j)
    print("\n[*] Sample Dialect Transformations (Z -> J):")
    cursor.execute('''
        SELECT french, lingala FROM lingohut_flashcards 
        WHERE lingala LIKE '%j%' LIMIT 5
    ''')
    for fr, lin in cursor.fetchall():
        print(f"    - FR: '{fr}' => LIN: '{lin}'")
        
    print(f"\n[+] Database compiled successfully into portable file: {DB_NAME}")
    print("="*50)


if __name__ == "__main__":
    db_conn = init_db()
    try:
        scrape_lexilogos(db_conn)
        map_raw_to_lingohut(db_conn)
        print_db_summary(db_conn)
    finally:
        db_conn.close()
