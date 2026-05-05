import sqlite3
import csv
import os
import sys

DB_NAME = "congolang_lessons_core.db"

def check_and_export():
    if not os.path.exists(DB_NAME):
        print(f"[-] Error: Database '{DB_NAME}' not found.")
        print("Please ensure you have run pipeline.py and hf_expansion_pipeline.py first.")
        sys.exit(1)

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        print("\n" + "="*50)
        print(" DATABASE DIAGNOSTICS & REPORT ")
        print("="*50)

        # 1. Flashcards Overview
        cursor.execute("SELECT COUNT(*) FROM lingohut_flashcards")
        total_cards = cursor.fetchone()[0]
        print(f"[*] Total Pedagogical Flashcards Active: {total_cards}")

        # 2. Database Tables Overview
        tables = ['lexilogos_raw_corpus', 'huggingface_massive_corpus', 'lingohut_lessons', 'lingohut_flashcards']
        print("\n[*] Table Row Counts:")
        for t in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                print(f"    - {t}: {cursor.fetchone()[0]}")
            except sqlite3.OperationalError:
                print(f"    - {t}: Table Not Found (Not generated yet?)")

        # 3. Lesson Breakdown
        print("\n[*] Sentences Mapped per Lesson Theme:")
        cursor.execute('''
            SELECT ll.lesson_id, ll.topic_name, COUNT(lf.card_id) 
            FROM lingohut_lessons ll
            LEFT JOIN lingohut_flashcards lf ON ll.lesson_id = lf.lesson_id
            GROUP BY ll.lesson_id
            ORDER BY ll.lesson_id ASC
        ''')
        for l_id, topic, count in cursor.fetchall():
             print(f"    - {topic} (ID:{l_id}): {count} cards")

        # 4. Dialect Verification (Quick Check)
        cursor.execute("SELECT COUNT(*) FROM lingohut_flashcards WHERE lingala LIKE '%j%'")
        z_to_j_count = cursor.fetchone()[0]
        print(f"\n[*] Dialect Triggers: Detected {z_to_j_count} records containing 'j' (Z->J shift)")

        cursor.execute("SELECT COUNT(*) FROM lingohut_flashcards WHERE lingala LIKE '%ve%'")
        ve_count = cursor.fetchone()[0]
        print(f"[*] Dialect Triggers: Detected {ve_count} records containing 've' (ko->ve shift)")

        # Export to CSV
        export_file = "congolang_flashcards_export.csv"
        print(f"\n[+] Exporting flashcards to {export_file}...")
        
        cursor.execute('''
            SELECT lf.card_id, ll.topic_name, lf.word_stem, lf.french, lf.lingala, lf.audio_tag
            FROM lingohut_flashcards lf
            JOIN lingohut_lessons ll ON lf.lesson_id = ll.lesson_id
            ORDER BY lf.lesson_id ASC, lf.card_id ASC
        ''')
        
        rows = cursor.fetchall()
        with open(export_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Card ID", "Lesson Topic", "Word Stem", "French", "Target Language (Lingala/Kituba)", "Audio Tag"])
            writer.writerows(rows)
            
        print(f"[+] Export successful! Wrote {len(rows)} rows into {export_file}.")
        print("="*50 + "\n")

    except Exception as e:
        print(f"[-] Error during database connection/export: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_and_export()
