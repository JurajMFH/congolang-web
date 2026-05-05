import sqlite3
import json
import socket
import logging
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from google.api_core import exceptions as google_exceptions

# --------------------------------------------------------------------------
# LOGGING CONFIGURATION
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FirestoreSyncService")

# --------------------------------------------------------------------------
# CONFIGURATION & PATHS
# --------------------------------------------------------------------------
DB_PATH = "congolang_pan_congo.db"
# Dynamically locate credentials file in root
CREDENTIALS_FILE = 'congolang-firebase-adminsdk-fbsvc-7e48d22ffb.json'

def setup_outbox_table(conn):
    """
    Creates the outbox table for offline fallback if it doesn't already exist.
    Stores pending operations (SET, UPDATE, DELETE, ADD).
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS firestore_outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_name TEXT NOT NULL,
            document_id TEXT,
            payload TEXT NOT NULL,
            operation TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'PENDING'
        );
    """)
    conn.commit()

def check_firestore_connectivity():
    """
    Diagnostic Function: Quick socket-based test to detect if local Firewall, 
    Antivirus, or VPN is blocking the SSL/TCP handshake to firestore.googleapis.com.
    """
    try:
        # Port 443 for secure SSL/TLS connection
        socket.create_connection(("firestore.googleapis.com", 443), timeout=3)
        return True
    except (socket.timeout, socket.error, ConnectionRefusedError, ConnectionAbortedError) as e:
        logger.warning(f"Firestore connectivity check failed (Firewall/VPN blocking?): {e}")
        return False

def initialize_firebase():
    """
    Initializes Firebase Admin SDK with comprehensive error handling.
    Specifically catches TransportError and TCP aborts.
    Returns: firestore.client instance or None if offline.
    """
    if not check_firestore_connectivity():
        logger.warning("Firestore sync blocked by local host network. Switching to local-only mode.")
        return None

    try:
        if not firebase_admin._apps:
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"Credentials file not found: {CREDENTIALS_FILE}")
                return None
            
            cred = credentials.Certificate(CREDENTIALS_FILE)
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        logger.info("Firebase Firestore client successfully initialized.")
        return db
    except (ConnectionAbortedError, google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded) as e:
        logger.error(f"Network transport error during Firebase init: {e}. Switching to offline fallback.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during Firebase initialization: {e}")
        return None

def queue_for_sync(collection, payload, doc_id=None, operation='ADD'):
    """
    Outbox Queue Logic: Commits data to local SQLite outbox for future synchronization.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        setup_outbox_table(conn)
        cursor = conn.cursor()
        
        payload_str = json.dumps(payload)
        cursor.execute("""
            INSERT INTO firestore_outbox (collection_name, document_id, payload, operation, status)
            VALUES (?, ?, ?, ?, 'PENDING')
        """, (collection, doc_id, payload_str, operation))
        
        conn.commit()
        logger.info(f"Data safely committed to local outbox queue. Operation: {operation} -> {collection}")
    except Exception as e:
        logger.error(f"Error writing to SQLite outbox: {e}")
    finally:
        conn.close()

def sync_to_firestore(db_client, collection, payload, doc_id=None, operation='ADD'):
    """
    Attempts to write to Firestore. If any connection or transport error occurs,
    it intercepts the error and falls back to the local outbox.
    """
    if db_client is None:
        logger.warning("Firestore client is offline. Bypassing cloud sync, using local outbox.")
        queue_for_sync(collection, payload, doc_id, operation)
        return False

    try:
        col_ref = db_client.collection(collection)
        if operation == 'ADD' or (operation == 'SET' and doc_id is None):
            col_ref.add(payload)
        elif operation == 'SET':
            col_ref.document(doc_id).set(payload)
        elif operation == 'UPDATE':
            col_ref.document(doc_id).update(payload)
        elif operation == 'DELETE':
            col_ref.document(doc_id).delete()
            
        logger.info(f"Successfully synced to cloud: {operation} -> {collection}/{doc_id if doc_id else '(new)'}")
        return True
    except (ConnectionAbortedError, google_exceptions.GoogleAPICallError, Exception) as e:
        # Catching specific TCP aborts and transport errors
        logger.error(f"Firestore sync aborted or failed: {e}. Intercepting and switching to offline mode.")
        queue_for_sync(collection, payload, doc_id, operation)
        return False

def process_outbox(db_client):
    """
    Processes pending records from the local SQLite outbox and pushes them to cloud.
    Should be called periodically or when connection is restored.
    """
    if db_client is None or not check_firestore_connectivity():
        logger.info("Device is still offline. Skipping outbox processing.")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        setup_outbox_table(conn)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, collection_name, document_id, payload, operation FROM firestore_outbox WHERE status = 'PENDING'")
        pending_tasks = cursor.fetchall()
        
        if not pending_tasks:
            logger.info("Outbox is empty. Everything is synchronized.")
            return

        logger.info(f"Found {len(pending_tasks)} pending tasks for synchronization.")
        
        for task in pending_tasks:
            task_id, col, doc_id, payload_str, op = task
            payload = json.loads(payload_str)
            
            # Attempt sync
            success = sync_to_firestore(db_client, col, payload, doc_id, op)
            
            if success:
                # Mark as synced to prevent duplicates
                cursor.execute("UPDATE firestore_outbox SET status = 'SYNCED' WHERE id = ?", (task_id,))
                conn.commit()
                logger.info(f"Task {task_id} successfully synchronized and cleared.")
                
    except Exception as e:
        logger.error(f"Error processing outbox: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Example diagnostic run
    print("--- Antigravity Firestore Diagnostic ---")
    db = initialize_firebase()
    if db:
        print("[+] Online: Connection established.")
        # Try a sample sync to verify
        # sync_to_firestore(db, "diagnostics", {"timestamp": datetime.now().isoformat()}, doc_id="heartbeat", operation="SET")
        process_outbox(db)
    else:
        print("[-] Offline: Connectivity blocked. Offline-first mode active.")
