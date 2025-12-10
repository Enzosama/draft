import sqlite3
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

DB_PATH = BASE_DIR / "backend" / "cyber_chat.sqlite"

def add_cyber_books():
    """Add cybersecurity books to the database"""
    print(f"Adding cybersecurity books to {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Define topics to add
        topics = [
            {
                "slug": "network-security",
                "name": "Network Security",
                "topic_type": "both",
                "domain": "Network",
                "level": "intermediate",
                "description": "Network attack and defense techniques, network security fundamentals"
            },
            {
                "slug": "cybersecurity-fundamentals",
                "name": "Cybersecurity Fundamentals",
                "topic_type": "both",
                "domain": "General",
                "level": "beginner",
                "description": "Core cybersecurity concepts, best practices, and fundamental knowledge"
            }
        ]
        
        # Insert topics if they don't exist
        topic_ids = {}
        for topic in topics:
            cursor = conn.execute(
                "SELECT id FROM cyber_topics WHERE slug = ?",
                (topic["slug"],)
            )
            existing = cursor.fetchone()
            
            if existing:
                topic_ids[topic["slug"]] = existing[0]
                print(f"Topic '{topic['name']}' already exists with ID {existing[0]}")
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO cyber_topics (slug, name, topic_type, domain, level, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        topic["slug"],
                        topic["name"],
                        topic["topic_type"],
                        topic["domain"],
                        topic["level"],
                        topic["description"]
                    )
                )
                topic_ids[topic["slug"]] = cursor.lastrowid
                print(f"Created topic '{topic['name']}' with ID {cursor.lastrowid}")
        
        # Define books to add
        books = [
            {
                "topic_slug": "cybersecurity-fundamentals",
                "title": "CYBERSECURITY HANDBOOK",
                "resource_type": "book",
                "source": "Google Drive",
                "file_url": "https://drive.google.com/file/d/13tjRSgEMUSheQjJuaEGOMjoJehpSee-2/view?usp=sharing",
                "is_offensive": True,
                "is_defensive": True,
                "difficulty": "beginner",
                "tags": "handbook, fundamentals, cybersecurity",
                "summary": "Comprehensive cybersecurity handbook covering fundamental concepts and practices"
            },
            {
                "topic_slug": "network-security",
                "title": "Network Defense: The Attacks of Today and How Can We Improve?",
                "resource_type": "book",
                "source": "Google Drive",
                "file_url": "https://drive.google.com/file/d/1L5w5QquHckWFPkU8kuCZ9chtm0GRpXsI/view?usp=sharing",
                "is_offensive": False,
                "is_defensive": True,
                "difficulty": "intermediate",
                "tags": "network defense, modern attacks, defense strategies",
                "summary": "Analysis of modern network attacks and defensive strategies for improvement"
            },
            {
                "topic_slug": "network-security",
                "title": "Network Attack and Defense",
                "resource_type": "book",
                "source": "Google Drive",
                "file_url": "https://drive.google.com/file/d/1gFMKg-8OfB4r_0OKBVpB-PpnWSRcc6xr/view?usp=sharing",
                "is_offensive": True,
                "is_defensive": True,
                "difficulty": "intermediate",
                "tags": "network attacks, network defense, offensive security, defensive security",
                "summary": "Comprehensive guide covering both offensive and defensive network security techniques"
            }
        ]
        
        # Insert books
        for book in books:
            topic_id = topic_ids[book["topic_slug"]]
            
            # Check if book already exists
            cursor = conn.execute(
                "SELECT id FROM cyber_resources WHERE title = ? AND topic_id = ?",
                (book["title"], topic_id)
            )
            existing = cursor.fetchone()
            
            if existing:
                print(f"Book '{book['title']}' already exists, skipping")
                continue
            
            cursor = conn.execute(
                """
                INSERT INTO cyber_resources (
                    topic_id, title, resource_type, source, file_url,
                    is_offensive, is_defensive, difficulty, tags, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    topic_id,
                    book["title"],
                    book["resource_type"],
                    book["source"],
                    book["file_url"],
                    book["is_offensive"],
                    book["is_defensive"],
                    book["difficulty"],
                    book["tags"],
                    book["summary"]
                )
            )
            print(f"Added book '{book['title']}' with ID {cursor.lastrowid}")
        
        # Commit transaction
        conn.commit()
        print("\n✓ Successfully added cybersecurity books to the database")
        
        # Display summary
        cursor = conn.execute("SELECT COUNT(*) FROM cyber_topics")
        topic_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM cyber_resources")
        resource_count = cursor.fetchone()[0]
        
        print(f"\nDatabase Summary:")
        print(f"- Total topics: {topic_count}")
        print(f"- Total resources: {resource_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error adding books: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    add_cyber_books()
