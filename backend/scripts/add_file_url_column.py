#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "cyber_chat.sqlite"

def add_file_url_column():
    """Add file_url column to cyber_resources table if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(cyber_resources)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'file_url' not in columns:
            print("Adding file_url column to cyber_resources table...")
            cursor.execute("ALTER TABLE cyber_resources ADD COLUMN file_url TEXT")
            conn.commit()
            print("✓ Successfully added file_url column")
        else:
            print("✓ file_url column already exists")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_file_url_column()
