"""
Khởi tạo SQLite backend riêng cho chatbot an ninh mạng (tấn công & phòng thủ).

Tạo file DB: backend/cyber_chat.sqlite
Schema: backend/database/cyber_schema.sql
"""

import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

DB_PATH = PROJECT_ROOT / "backend" / "cyber_chat.sqlite"
SCHEMA_PATH = BASE_DIR / "database" / "cyber_schema.sql"


def init_cyber_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print(f"[OK] Initialized cyber security chatbot DB at: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_cyber_db()


