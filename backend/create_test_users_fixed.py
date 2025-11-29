#!/usr/bin/env python3
"""
Create/fix test users using backend's password hashing
Run this from backend directory or with: python -m backend.create_test_users_fixed
"""

import asyncio
import os
import sys

# Ensure we can import backend modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import db
from backend.utils import get_password_hash, verify_password

async def create_or_update_test_users():
    """Create or update test users with correct password hashes"""
    print("🔧 Creating/updating test users with backend password hashing...\n")
    
    # Test Student Account
    student_email = "student@test.com"
    student_password = "student123"
    
    # Check if exists
    existing = await db.fetch_one("SELECT id, email, role FROM users WHERE email = ?", [student_email])
    
    if existing:
        print(f"⚠️  Student exists, updating password...")
        password_hash = get_password_hash(student_password)
        await db.update(
            "UPDATE users SET password_hash = ?, is_active = 1 WHERE email = ?",
            [password_hash, student_email]
        )
        
        # Verify
        user = await db.fetch_one("SELECT password_hash FROM users WHERE email = ?", [student_email])
        if user and verify_password(student_password, user["password_hash"]):
            print(f"✅ Student password updated and verified")
        else:
            print(f"❌ Student password verification failed!")
    else:
        print(f"📝 Creating new student...")
        password_hash = get_password_hash(student_password)
        try:
            user_id = await db.insert(
                """INSERT INTO users (fullname, email, phone, password_hash, role, is_active) 
                   VALUES (?, ?, ?, ?, 'student', 1)""",
                ["Học Sinh Test", student_email, "0123456789", password_hash]
            )
            print(f"✅ Student created (ID: {user_id})")
        except Exception as e:
            print(f"❌ Error: {e}")
            # Try without phone
            try:
                user_id = await db.insert(
                    """INSERT INTO users (fullname, email, password_hash, role, is_active) 
                       VALUES (?, ?, ?, 'student', 1)""",
                    ["Học Sinh Test", student_email, password_hash]
                )
                print(f"✅ Student created without phone (ID: {user_id})")
            except Exception as e2:
                print(f"❌ Error: {e2}")
    
    print("\n" + "="*50 + "\n")
    
    # Test Teacher Account
    teacher_email = "teacher@test.com"
    teacher_password = "teacher123"
    
    # Check if exists
    existing = await db.fetch_one("SELECT id, email, role FROM users WHERE email = ?", [teacher_email])
    
    if existing:
        print(f"⚠️  Teacher exists, updating password...")
        password_hash = get_password_hash(teacher_password)
        await db.update(
            "UPDATE users SET password_hash = ?, is_active = 1 WHERE email = ?",
            [password_hash, teacher_email]
        )
        
        # Verify
        user = await db.fetch_one("SELECT password_hash FROM users WHERE email = ?", [teacher_email])
        if user and verify_password(teacher_password, user["password_hash"]):
            print(f"✅ Teacher password updated and verified")
        else:
            print(f"❌ Teacher password verification failed!")
    else:
        print(f"📝 Creating new teacher...")
        password_hash = get_password_hash(teacher_password)
        try:
            user_id = await db.insert(
                """INSERT INTO users (fullname, email, phone, password_hash, role, is_active) 
                   VALUES (?, ?, ?, ?, 'teacher', 1)""",
                ["Giáo Viên Test", teacher_email, "0987654321", password_hash]
            )
            print(f"✅ Teacher created (ID: {user_id})")
        except Exception as e:
            print(f"❌ Error: {e}")
            # Try without phone
            try:
                user_id = await db.insert(
                    """INSERT INTO users (fullname, email, password_hash, role, is_active) 
                       VALUES (?, ?, ?, 'teacher', 1)""",
                    ["Giáo Viên Test", teacher_email, password_hash]
                )
                print(f"✅ Teacher created without phone (ID: {user_id})")
            except Exception as e2:
                print(f"❌ Error: {e2}")
    
    print("\n" + "="*50)
    print("\n📋 Test Accounts Summary:")
    print(f"\n👨‍🎓 STUDENT:")
    print(f"   Email: {student_email}")
    print(f"   Password: {student_password}")
    print(f"\n👨‍🏫 TEACHER:")
    print(f"   Email: {teacher_email}")
    print(f"   Password: {teacher_password}")
    print("\n✅ Done! Try logging in now.")

if __name__ == "__main__":
    asyncio.run(create_or_update_test_users())



