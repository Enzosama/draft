import sqlite3
import json
import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

DB_PATH = BASE_DIR / "backend" / "cyber_chat.sqlite"
EXPORT_PATH = BASE_DIR / "backend" / "cyber_topics_export.json"

def export_topics():
    print(f"Exporting cyber topics from {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Check if we have data
    cursor = conn.execute("SELECT count(*) FROM cyber_topics")
    count = cursor.fetchone()[0]
    
    data = []
    
    if count > 0:
        print(f"Found {count} topics in database. Exporting...")
        topics = conn.execute("SELECT * FROM cyber_topics").fetchall()
        for topic in topics:
            t_dict = dict(topic)
            # Get resources for this topic
            resources = conn.execute("SELECT * FROM cyber_resources WHERE topic_id = ?", (t_dict['id'],)).fetchall()
            t_dict['resources'] = [dict(r) for r in resources]
            data.append(t_dict)
    else:
        print("Database table 'cyber_topics' is empty. Generating sample structure...")
        data = [
            {
                "slug": "web-security",
                "name": "Web Security",
                "topic_type": "both",
                "domain": "Web",
                "level": "beginner",
                "description": "Bảo mật ứng dụng Web, bao gồm các lỗ hổng phổ biến như SQL Injection, XSS, CSRF.",
                "resources": [
                    {
                        "title": "OWASP Top 10",
                        "resource_type": "article",
                        "source": "https://owasp.org/www-project-top-ten/",
                        "is_offensive": True,
                        "is_defensive": True,
                        "difficulty": "beginner",
                        "tags": "owasp,web,vulnerability",
                        "summary": "Top 10 lỗ hổng bảo mật web phổ biến nhất."
                    },
                    {
                        "title": "PortSwigger Web Security Academy",
                        "resource_type": "lab",
                        "source": "https://portswigger.net/web-security",
                        "is_offensive": True,
                        "is_defensive": False,
                        "difficulty": "intermediate",
                        "tags": "lab,burpsuite,practice",
                        "summary": "Các bài lab thực hành tấn công web miễn phí."
                    }
                ]
            },
            {
                "slug": "network-security",
                "name": "Network Security",
                "topic_type": "defense",
                "domain": "Network",
                "level": "intermediate",
                "description": "Bảo mật hệ thống mạng, cấu hình Firewall, IDS/IPS và giám sát lưu lượng.",
                "resources": [
                    {
                        "title": "Wireshark Network Analysis",
                        "resource_type": "tool",
                        "source": "https://www.wireshark.org/",
                        "is_offensive": False,
                        "is_defensive": True,
                        "difficulty": "intermediate",
                        "tags": "network,analysis,packet",
                        "summary": "Phân tích gói tin mạng để phát hiện bất thường."
                    }
                ]
            },
            {
                "slug": "malware-analysis",
                "name": "Malware Analysis",
                "topic_type": "defense",
                "domain": "Malware",
                "level": "advanced",
                "description": "Phân tích mã độc, kỹ thuật dịch ngược (Reverse Engineering) và phân tích hành vi.",
                "resources": []
            },
            {
                "slug": "pentest-basics",
                "name": "Penetration Testing Basics",
                "topic_type": "attack",
                "domain": "General",
                "level": "beginner",
                "description": "Các kiến thức cơ bản về kiểm thử xâm nhập, quy trình và công cụ.",
                "resources": []
            }
        ]

    # Write to JSON file
    with open(EXPORT_PATH, "w", encoding="utf-8") as f:
        json.dump({"topics": data}, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully exported to {EXPORT_PATH}")
    conn.close()

if __name__ == "__main__":
    export_topics()
