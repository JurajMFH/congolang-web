import sqlite3
import json
import os

DB_NAME = "congolang_pan_congo.db"
OUTPUT_PATH = "public/assets/data/lessons.json"

def export_bundle():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Query all phrases
    c.execute("SELECT * FROM bantu_phrases ORDER BY id ASC")
    rows = c.fetchall()
    
    # Group by french_original
    phrases_map = {}
    for row in rows:
        fr = row['french_original']
        if fr not in phrases_map:
            phrases_map[fr] = {
                "id": len(phrases_map) + 1,
                "french": fr,
                "translations": []
            }
        
        phrases_map[fr]["translations"].append({
            "lang": row['language_code'],
            "text": row['translated_text'],
            "audio": f"assets/audio/{row['language_code']}_{row['translated_text'].lower().replace(' ', '_').replace('?', '')}.mp3",
            "metadata": {
                "root": row['root_word'],
                "prefix": row['class_prefix'],
                "context": row['cultural_context'],
                "tone": row['tone_marker']
            }
        })
    
    bundle = {
        "lesson_id": 1,
        "topic": "Salutations & Introductions",
        "phrases": list(phrases_map.values())
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully exported {len(bundle['phrases'])} phrases to {OUTPUT_PATH}")
    conn.close()

if __name__ == "__main__":
    export_bundle()
