import sqlite3
import json
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

DB_PATH = BASE_DIR / "backend" / "cyber_chat.sqlite"
IMPORT_PATH = BASE_DIR / "backend" / "cyber_topics_export.json"

def import_topics():
    print(f"Importing cyber topics from {IMPORT_PATH} to {DB_PATH}...")
    
    if not os.path.exists(IMPORT_PATH):
        print(f"Error: Import file not found at {IMPORT_PATH}")
        return
        
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        with open(IMPORT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            topics = data.get("topics", [])
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Clear existing data
        print("Clearing existing topics and resources...")
        conn.execute("DELETE FROM cyber_resources")
        conn.execute("DELETE FROM cyber_topics")
        
        # Insert new data
        print(f"Inserting {len(topics)} topics...")
        
        for topic in topics:
            # Insert topic
            cursor = conn.execute(
                """
                INSERT INTO cyber_topics (slug, name, topic_type, domain, level, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    topic.get("slug"),
                    topic.get("name"),
                    topic.get("topic_type", "other"),
                    topic.get("domain"),
                    topic.get("level"),
                    topic.get("description")
                )
            )
            topic_id = cursor.lastrowid
            
            # Insert resources
            resources = topic.get("resources", [])
            if resources:
                for res in resources:
                    conn.execute(
                        """
                        INSERT INTO cyber_resources (
                            topic_id, title, resource_type, source, file_url,
                            is_offensive, is_defensive, difficulty, tags, summary
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            topic_id,
                            res.get("title"),
                            res.get("resource_type"),
                            res.get("source"),
                            res.get("file_url"),
                            res.get("is_offensive", False),
                            res.get("is_defensive", False),
                            res.get("difficulty"),
                            res.get("tags"),
                            res.get("summary")
                        )
                    )
        
        conn.commit()
        print("Import completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error importing data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    import_topics()
