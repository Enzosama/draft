import os
import sys
import json
import asyncio

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import db  # type: ignore

async def seed_from_file(path: str) -> None:
    if not os.path.isabs(path):
        path = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(path):
        print(json.dumps({"ok": False, "error": "file_not_found", "path": path}))
        return

    inserted = 0
    skipped = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception as e:
                skipped += 1
                continue

            title = item.get("title")
            author = item.get("author")
            date = item.get("date")
            subject = item.get("subject")
            category = item.get("category")
            description = item.get("description")
            views = item.get("views", 0)
            downloads = item.get("downloads", 0)
            class_field = item.get("class")
            specialized = item.get("specialized")
            file_url = item.get("file_url") or item.get("fileUrl")
            user_id = item.get("user_id")

            if not (title and author and date and subject and category):
                skipped += 1
                continue

            exists = await db.fetch_one(
                "SELECT id FROM posts WHERE title = ? AND author = ? AND date = ?",
                [title, author, date]
            )
            if exists:
                skipped += 1
                continue

            # Validate user_id against users table to avoid FK errors
            user_id_final = None
            if user_id is not None:
                u = await db.fetch_one("SELECT id FROM users WHERE id = ?", [user_id])
                if u:
                    user_id_final = user_id

            await db.insert(
                (
                    "INSERT INTO posts (title, author, \"date\", subject, category, description, "
                    "views, downloads, \"class\", specialized, file_url, user_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                [
                    title, author, date, subject, category, description,
                    views, downloads, class_field, specialized, file_url, user_id_final,
                ]
            )
            inserted += 1

    total_row = await db.fetch_one("SELECT COUNT(*) AS total FROM posts")
    print(json.dumps({"ok": True, "inserted": inserted, "skipped": skipped, "posts_total": (total_row or {}).get("total", 0)}))

async def main():
    rel = os.getenv("POSTS_FILE", "post.json")
    await seed_from_file(rel)

if __name__ == "__main__":
    asyncio.run(main())