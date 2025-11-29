#!/usr/bin/env python3
"""
Setup admin user for testing
"""

import asyncio
import os
import sys

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import settings
from backend.database import db
from backend.utils import get_password_hash

async def setup_admin():
    """Setup admin user"""
    print("🔧 Setting up admin user...")
    
    # Check if admin already exists
    existing = await db.fetch_one("SELECT id FROM users WHERE email = ?", ["admin@test.com"])
    if existing:
        print("✅ Admin user already exists")
        return
    
    # Create admin user
    password_hash = get_password_hash("admin123")
    result = await db.execute(
        """INSERT INTO users (fullname, email, phone, password_hash, role, is_active) 
           VALUES (?, ?, ?, ?, 'admin', 1)""",
        ["Admin User", "admin@test.com", "0123456789", password_hash]
    )
    
    print("✅ Admin user created successfully")
    print("📧 Email: admin@test.com")
    print("🔑 Password: admin123")

if __name__ == "__main__":
    asyncio.run(setup_admin())