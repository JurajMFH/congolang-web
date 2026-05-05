import sqlite3
import concurrent.futures
import time
import random

DB_PATH = "congolang_pan_congo.db"
NUM_WORKERS = 15        # Simulujeme 15 paralelne bežiacich zberačov
INSERTS_PER_WORKER = 200 # Každý zberač zapíše 200 viet

def simulate_harvester_writes(worker_id):
    try:
        # Timeout 30.0 je kľúčový pre WAL režim
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        cursor = conn.cursor()
        success_count = 0

        for i in range(INSERTS_PER_WORKER):
            time.sleep(random.uniform(0.001, 0.05))
            
            # Zápis do správnej tabuľky 'records' s reálnymi stĺpcami vašej DB
            cursor.execute('''
                INSERT INTO records (language_code, normalized_text, region_target, register_type, status)
                VALUES (?, ?, ?, ?, ?)
            ''', ("mkw", f"Testovacia veta {i} z vlákna {worker_id}", "ROC_BRAZZAVILLE", "TEST", "UNVERIFIED"))
            conn.commit()
            success_count += 1

        conn.close()
        return f"✅ Vlákno {worker_id}: Úspešne zapísaných {success_count} riadkov."
    
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            return f"❌ Vlákno {worker_id}: Zámok databázy (Database locked)."
        else:
            return f"❌ Vlákno {worker_id}: SQL CHYBA: {e}"
    except Exception as e:
        return f"❌ Vlákno {worker_id}: Iná chyba: {e}"

if __name__ == "__main__":
    print(f"🚀 Spúšťam záťažový test: {NUM_WORKERS} paralelných vlákien...")
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        results = list(executor.map(simulate_harvester_writes, range(NUM_WORKERS)))

    for res in results:
        print(res)

    print("🧹 Čistím testovacie dáta...")
    clean_conn = sqlite3.connect(DB_PATH)
    # Vymažeme len testovacie dáta, aby sme nepoškodili reálny korpus
    clean_conn.execute("DELETE FROM records WHERE register_type = 'TEST'")
    clean_conn.commit()
    clean_conn.close()

    print(f"⏱️ Test dokončený za {time.time() - start_time:.2f} sekúnd.")