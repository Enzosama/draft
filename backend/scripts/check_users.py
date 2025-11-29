import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "cyber_chat.sqlite"

def check_users():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, fullname, email, role, is_active FROM users")
        users = cursor.fetchall()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user['id']}, Email: {user['email']}, Role: '{user['role']}', Active: {user['is_active']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_users()
