#!/usr/bin/env python3
"""
Script to migrate network materials from db.sqlite to cyber_chat.sqlite
"""

import sqlite3
import sys
from pathlib import Path

def migrate_network_materials():
    # Database paths
    source_db = Path("/Users/enzo/Downloads/perl_python/backend/db.sqlite")
    target_db = Path("/Users/enzo/Downloads/perl_python/backend/cyber_chat.sqlite")
    
    if not source_db.exists():
        print(f"❌ Source database not found: {source_db}")
        return False
    
    if not target_db.exists():
        print(f"❌ Target database not found: {target_db}")
        return False
    
    try:
        # Connect to both databases
        source_conn = sqlite3.connect(source_db)
        source_conn.row_factory = sqlite3.Row
        target_conn = sqlite3.connect(target_db)
        target_conn.row_factory = sqlite3.Row
        
        # Get network materials from source database (posts with file_url containing drive.google.com)
        source_cursor = source_conn.cursor()
        target_cursor = target_conn.cursor()
        
        # Check if posts table exists in target
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts'")
        if not target_cursor.fetchone():
            print("❌ Posts table not found in target database")
            return False
        
        # Get network materials from source
        source_cursor.execute("""
            SELECT title, author, date, subject, category, description, 
                   views, downloads, class, specialized, file_url, user_id, 
                   created_at, updated_at
            FROM posts 
            WHERE file_url LIKE '%drive.google.com%'
            ORDER BY id DESC
        """)
        
        network_materials = source_cursor.fetchall()
        
        if not network_materials:
            print("❌ No network materials found in source database")
            return False
        
        print(f"📊 Found {len(network_materials)} network materials to migrate")
        
        # Insert into target database
        inserted_count = 0
        for material in network_materials:
            try:
                target_cursor.execute("""
                    INSERT INTO posts (
                        title, author, date, subject, category, description, 
                        views, downloads, class, specialized, file_url, user_id, 
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    material['title'],
                    material['author'],
                    material['date'],
                    material['subject'],
                    material['category'],
                    material['description'],
                    material['views'],
                    material['downloads'],
                    material['class'],
                    material['specialized'],
                    material['file_url'],
                    material['user_id'],
                    material['created_at'],
                    material['updated_at']
                ))
                inserted_count += 1
                print(f"✅ Migrated: {material['title']}")
            except sqlite3.IntegrityError as e:
                print(f"⚠️  Skipped (likely duplicate): {material['title']}")
        
        # Commit changes
        target_conn.commit()
        
        # Verify migration
        target_cursor.execute("SELECT COUNT(*) as total FROM posts WHERE file_url LIKE '%drive.google.com%'")
        result = target_cursor.fetchone()
        total_in_target = result['total'] if result else 0
        
        print(f"\n📈 Migration complete!")
        print(f"✅ Inserted {inserted_count} network materials")
        print(f"📊 Total network materials in target: {total_in_target}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False
    finally:
        # Close connections
        source_conn.close()
        target_conn.close()

if __name__ == "__main__":
    success = migrate_network_materials()
    sys.exit(0 if success else 1)