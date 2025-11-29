import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

OLD_DB_PATH = BASE_DIR / "backend" / "db.sqlite"
NEW_DB_PATH = BASE_DIR / "backend" / "cyber_chat.sqlite"
SCHEMA_PATH = BASE_DIR / "backend" / "database" / "cyber_schema.sql"

def migrate():
    print(f"Starting migration from {OLD_DB_PATH} to {NEW_DB_PATH}")
    
    if not os.path.exists(OLD_DB_PATH):
        print(f"Error: Old database not found at {OLD_DB_PATH}")
        return

    # 1. Initialize new DB with schema
    print("Initializing new database schema...")
    if os.path.exists(NEW_DB_PATH):
        os.remove(NEW_DB_PATH)
        print("Removed existing new database file.")
        
    conn_new = sqlite3.connect(NEW_DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn_new.executescript(schema_sql)
    conn_new.commit()
    print("Schema initialized.")

    # 2. Connect to old DB
    conn_old = sqlite3.connect(OLD_DB_PATH)
    conn_old.row_factory = sqlite3.Row

    # 3. Migrate Tables
    tables_to_migrate = [
        "users", 
        "subjects", 
        "posts", 
        "exams", 
        "password_reset_tokens",
        "questions",
        "question_options",
        "question_answers",
        "exam_questions"
    ]

    for table in tables_to_migrate:
        print(f"Migrating table: {table}...")
        try:
            # Check if table exists in old DB
            cursor = conn_old.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not cursor.fetchone():
                print(f"  Skipping {table} (not found in old DB)")
                continue

            # Get columns from new DB to ensure compatibility
            cursor = conn_new.execute(f"PRAGMA table_info({table})")
            new_columns = [row[1] for row in cursor.fetchall()]
            new_columns_str = ", ".join(new_columns)
            
            # Select data from old DB
            # We select * and then filter/map in python if needed, but for now assuming mostly compatible
            # Actually, safer to select only columns that exist in both, or handle mismatches
            
            # Get columns from old DB
            cursor = conn_old.execute(f"PRAGMA table_info({table})")
            old_columns = [row[1] for row in cursor.fetchall()]
            
            # Find common columns
            common_columns = [col for col in new_columns if col in old_columns]
            common_columns_str = ", ".join(common_columns)
            placeholders = ", ".join(["?"] * len(common_columns))
            
            if not common_columns:
                print(f"  Skipping {table} (no common columns)")
                continue

            # Fetch data
            rows = conn_old.execute(f"SELECT {common_columns_str} FROM {table}").fetchall()
            
            if not rows:
                print(f"  No data in {table}")
                continue
                
            # Insert into new DB
            conn_new.executemany(
                f"INSERT INTO {table} ({common_columns_str}) VALUES ({placeholders})",
                [tuple(row) for row in rows]
            )
            conn_new.commit()
            print(f"  Migrated {len(rows)} rows for {table}")

        except Exception as e:
            print(f"  Error migrating {table}: {e}")

    # 4. Cleanup
    conn_old.close()
    conn_new.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
