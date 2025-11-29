import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "cyber_chat.sqlite"

def check_tables():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_tokens'")
        table = cursor.fetchone()
        if table:
            print("Table 'password_reset_tokens' exists.")
        else:
            print("Table 'password_reset_tokens' DOES NOT exist.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables()
