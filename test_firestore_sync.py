import sqlite3
import json
import os
import unittest
from unittest.mock import patch, MagicMock
from firestore_sync_service import (
    check_firestore_connectivity, 
    initialize_firebase, 
    sync_to_firestore, 
    process_outbox,
    DB_PATH
)

class TestFirestoreSyncService(unittest.TestCase):
    
    def setUp(self):
        # Ensure we use a clean test DB or a temporary one
        # For this test, we'll use the actual DB but clean up the outbox
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute("DROP TABLE IF EXISTS firestore_outbox")
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    @patch('socket.create_connection')
    def test_check_connectivity_success(self, mock_socket):
        # Mock success
        mock_socket.return_value = True
        self.assertTrue(check_firestore_connectivity())

    @patch('socket.create_connection')
    def test_check_connectivity_failure(self, mock_socket):
        # Mock failure (TCP Reset/Abort)
        mock_socket.side_effect = ConnectionAbortedError("Connection aborted")
        self.assertFalse(check_firestore_connectivity())

    @patch('firestore_sync_service.check_firestore_connectivity')
    def test_offline_fallback_queuing(self, mock_connectivity):
        # Simulate offline
        mock_connectivity.return_value = False
        
        # Initialize (should return None)
        db = initialize_firebase()
        self.assertIsNone(db)
        
        # Attempt sync (should trigger queue_for_sync)
        payload = {"test": "data"}
        success = sync_to_firestore(db, "test_collection", payload, operation='ADD')
        self.assertFalse(success)
        
        # Verify SQLite outbox has the record
        self.cursor.execute("SELECT collection_name, payload FROM firestore_outbox")
        row = self.cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "test_collection")
        self.assertEqual(json.loads(row[1]), payload)

    @patch('firestore_sync_service.check_firestore_connectivity')
    @patch('firestore_sync_service.sync_to_firestore')
    def test_process_outbox_when_back_online(self, mock_sync, mock_connectivity):
        # 1. Manually add a pending item to outbox
        self.cursor.execute("CREATE TABLE IF NOT EXISTS firestore_outbox (id INTEGER PRIMARY KEY, collection_name TEXT, document_id TEXT, payload TEXT, operation TEXT, status TEXT)")
        self.cursor.execute("INSERT INTO firestore_outbox (collection_name, payload, operation, status) VALUES (?, ?, ?, ?)", 
                           ("delayed_sync", json.dumps({"key": "val"}), "ADD", "PENDING"))
        self.conn.commit()
        
        # 2. Mock online status
        mock_connectivity.return_value = True
        mock_sync.return_value = True # Simulate successful cloud sync
        
        # 3. Process outbox
        mock_db = MagicMock()
        process_outbox(mock_db)
        
        # 4. Verify status updated to SYNCED
        self.cursor.execute("SELECT status FROM firestore_outbox WHERE collection_name = 'delayed_sync'")
        status = self.cursor.fetchone()[0]
        self.assertEqual(status, "SYNCED")

if __name__ == '__main__':
    unittest.main()
