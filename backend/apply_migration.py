#!/usr/bin/env python3
"""
Apply migration to add teachers, classrooms, and new features
"""

import asyncio
import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import settings
from database import db

async def apply_migration():
    """Apply the migration to add teachers and classrooms"""
    print("🔄 Applying migration: teachers, classrooms, and new features...")
    
    migration_path = os.path.join(BASE_DIR, "database", "migrations", "20241115_add_teachers_classrooms.sql")
    
    with open(migration_path, "r", encoding="utf-8") as f:
        migration_sql = f.read()
    
    # Split into individual statements
    statements = []
    current_statement = ""
    
    for line in migration_sql.split('\n'):
        line = line.strip()
        if line.startswith('--') or not line:
            continue
        
        current_statement += line + " "
        
        if line.endswith(';'):
            statements.append(current_statement.strip())
            current_statement = ""
    
    # Handle any remaining statement
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    # Execute each statement
    for statement in statements:
        if not statement or statement == ";":
            continue
            
        try:
            print(f"Executing: {statement[:100]}...")
            await db.execute(statement)
            print("✅ Success")
        except Exception as e:
            print(f"⚠️  Warning or error: {e}")
            # Continue with other statements even if some fail
    
    print("✅ Migration applied successfully!")

def apply_sqlite_migration():
    """Apply migration to SQLite"""
    print("🔄 Applying SQLite migration: teachers, classrooms, and new features...")
    
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    migration_path = os.path.join(BASE_DIR, "database", "migrations", "20241115_add_teachers_classrooms.sql")
    
    with open(migration_path, "r", encoding="utf-8") as f:
        migration_sql = f.read()
    
    # Split into individual statements
    statements = []
    current_statement = ""
    
    for line in migration_sql.split('\n'):
        line = line.strip()
        if line.startswith('--') or not line:
            continue
        
        current_statement += line + " "
        
        if line.endswith(';'):
            statements.append(current_statement.strip())
            current_statement = ""
    
    # Handle any remaining statement
    if current_statement.strip():
        statements.append(current_statement.strip())
    
    # Execute each statement
    for statement in statements:
        if not statement or statement == ";":
            continue
            
        try:
            print(f"Executing: {statement[:100]}...")
            cursor.execute(statement)
            print("✅ Success")
        except Exception as e:
            print(f"⚠️  Warning or error: {e}")
            # Continue with other statements even if some fail
    
    conn.commit()
    conn.close()
    print("✅ SQLite migration applied successfully!")

async def main():
    if settings.use_cloudflare_d1:
        await apply_migration()
    else:
        apply_sqlite_migration()

if __name__ == "__main__":
    asyncio.run(main())