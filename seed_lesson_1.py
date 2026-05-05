import sqlite3

DB_NAME = "congolang_pan_congo.db"

def seed_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Provisional AI translations for Lesson 1: Greetings
    # Format: (lang, french, translation, root, prefix, context, tone)
    seed_data = [
        # Lingala
        ('lin', 'Bonjour', 'Mbote', 'bota', 'm-', 'Universal greeting', 'High-Low'),
        ('lin', 'Comment ça va ?', 'Sango nini?', 'sango', '', 'Literally: "What news?"', 'Low-Low'),
        ('lin', 'Merci', 'Matondo', 'tondo', 'ma-', 'Root meaning gratitude', 'Low-Low'),
        
        # Kituba
        ('mkw', 'Bonjour', 'Mbote', 'bota', 'm-', 'Common with Lingala', 'Flat'),
        ('mkw', 'Comment ça va ?', 'Inki sango?', 'sango', 'inki', 'Kongo influenced', 'Flat'),
        ('mkw', 'Merci', 'Melesi', 'merci', '', 'Loan word from French', 'Flat'),
        
        # Lari
        ('ldi', 'Bonjour', 'Mbote', 'bota', 'm-', 'Shared Bantu root', 'High'),
        ('ldi', 'Comment ça va ?', 'Nuni sango?', 'sango', 'nuni', 'Specific to Lari/Pool', 'High'),
        ('ldi', 'Merci', 'Ntondele', 'tondo', 'n-', 'Pure Bantu form', 'High-Falling')
    ]
    
    records = []
    for lang, fr, tr, root, prefix, context, tone in seed_data:
        records.append((lang, fr, tr, root, prefix, context, tone, 'PROVISIONAL'))
        
    c.executemany('''
        INSERT INTO bantu_phrases (
            language_code, french_original, translated_text, 
            root_word, class_prefix, cultural_context, tone_marker, 
            verification_status
        ) VALUES (?,?,?,?,?,?,?,?)
    ''', records)
    
    conn.commit()
    print(f"Successfully seeded {len(records)} phrases into bantu_phrases.")
    conn.close()

if __name__ == "__main__":
    seed_data()
