import os
import sys
import json
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'backend', 'db.sqlite')
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'data.json')

INCLUDE_TABLES = [
    'subjects',
    'posts',
    'exams',
    'questions',
    'question_options',
    'question_answers',
    'exam_questions',
    'classrooms',
    'classroom_students',
    'classroom_posts',
    'classroom_exams',
    'notifications',
    'notification_reads',
]

def export():
    if not os.path.exists(DB_PATH):
        print(json.dumps({"ok": False, "error": "db_not_found", "path": DB_PATH}))
        return 1
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    data = {
        "metadata": {
            "source": "sqlite",
            "schema_version": "2024-11",
            "generated_at": datetime.now().isoformat(timespec='seconds')
        }
    }
    for name in INCLUDE_TABLES:
        try:
            cur.execute(f"SELECT * FROM {name}")
            rows = [dict(r) for r in cur.fetchall()]
            data[name] = rows
        except Exception:
            data[name] = []
    conn.close()
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(json.dumps({"ok": True, "output": OUTPUT_PATH}))
    return 0

if __name__ == '__main__':
    sys.exit(export())
