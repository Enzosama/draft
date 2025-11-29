#!/usr/bin/env python3
"""
Initialize database with schema
Supports both SQLite (local) and Cloudflare D1
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

async def init_d1():
    """Initialize Cloudflare D1"""
    print("📡 Initializing Cloudflare D1...")
    schema_path = os.path.join(BASE_DIR, "database", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    
    # Split into individual statements
    statements = [s.strip() for s in schema.split(";") if s.strip()]
    
    for statement in statements:
        try:
            await db.execute(statement)
            print(f"✅ Executed: {statement[:50]}...")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("✅ D1 initialized!")

def init_sqlite():
    """Initialize SQLite"""
    print("💾 Initializing SQLite...")
    
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    
    schema_path = os.path.join(BASE_DIR, "database", "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    
    conn.commit()
    conn.close()
    
    print(f"✅ SQLite initialized at: {db_path}")

async def main():
    if settings.use_cloudflare_d1:
        await init_d1()
    else:
        init_sqlite()

if __name__ == "__main__":
    asyncio.run(main())