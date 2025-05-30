#!/usr/bin/env python3
"""Test SQLite functionality directly."""

import sqlite3
import os
import json
from datetime import datetime

def main():
    print("Testing SQLite database directly...")
    
    # Set up database path
    db_path = os.path.expanduser("~/.mcp_screenshot/history.db")
    print(f"Database path: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Show tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")
    
    # Count rows
    cursor.execute("SELECT COUNT(*) FROM screenshots")
    count = cursor.fetchone()[0]
    print(f"Screenshots in database: {count}")
    
    # Insert a test record
    timestamp = datetime.now()
    print(f"Inserting test record at {timestamp}...")
    
    try:
        cursor.execute('''
            INSERT INTO screenshots 
            (filename, original_path, storage_path, file_hash, url, region, 
             timestamp, width, height, size_bytes, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            f"test_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg",
            "/test/path/original.jpg",
            "/test/path/stored.jpg",
            "testhash12345",
            None,
            None,
            timestamp.timestamp(),
            800,
            600,
            12345,
            json.dumps({"test": "metadata"})
        ))
        
        screenshot_id = cursor.lastrowid
        print(f"Inserted with ID: {screenshot_id}")
        
        # Commit the transaction
        conn.commit()
        print("Transaction committed")
        
        # Verify the insert
        cursor.execute("SELECT COUNT(*) FROM screenshots")
        count = cursor.fetchone()[0]
        print(f"Screenshots in database after insert: {count}")
        
        # Select the inserted record
        cursor.execute("SELECT id, filename FROM screenshots WHERE id = ?", (screenshot_id,))
        row = cursor.fetchone()
        print(f"Selected record: {row}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()