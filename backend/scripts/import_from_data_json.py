import os
import sys
import json
import sqlite3

BASE_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'backend', 'db.sqlite')
INPUT_PATH = os.path.join(PROJECT_ROOT, 'data.json')

ORDERED_COLLECTIONS = [
    'subjects',
    'classrooms',
    'posts',
    'exams',
    'questions',
    'question_options',
    'question_answers',
    'exam_questions',
    'classroom_students',
    'classroom_posts',
    'classroom_exams',
    'notifications',
    'notification_reads',
]

PRIMARY_KEYS = {
    'subjects': ['id'],
    'classrooms': ['id'],
    'posts': ['id'],
    'exams': ['id'],
    'questions': ['question_id'],
    'question_options': ['option_id'],
    'question_answers': ['answer_id'],
    'exam_questions': ['exam_id', 'question_id'],
    'classroom_students': ['classroom_id', 'student_id'],
    'classroom_posts': ['classroom_id', 'post_id'],
    'classroom_exams': ['classroom_id', 'exam_id'],
    'notifications': ['id'],
    'notification_reads': ['notification_id', 'student_id'],
}

EXCLUDED_TABLES = {'users', 'password_reset_tokens'}

def import_data():
    print("=" * 60)
    print("🚀 BẮT ĐẦU IMPORT DỮ LIỆU")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ LỖI: Không tìm thấy database tại: {DB_PATH}")
        print(json.dumps({"ok": False, "error": "db_not_found", "path": DB_PATH}))
        return 1
    
    if not os.path.exists(INPUT_PATH):
        print(f"❌ LỖI: Không tìm thấy file data tại: {INPUT_PATH}")
        print(json.dumps({"ok": False, "error": "input_not_found", "path": INPUT_PATH}))
        return 1
    
    print(f"📂 Đường dẫn database: {DB_PATH}")
    print(f"📂 Đường dẫn file data: {INPUT_PATH}")
    print()
    
    try:
        with open(INPUT_PATH, 'r', encoding='utf-8') as f:
            payload = json.load(f)
            print(f"✅ Đã đọc file JSON thành công")
    except Exception as e:
        print(f"❌ LỖI: Không thể đọc file JSON: {e}")
        return 1
    
    print()
    print("-" * 60)
    print("📊 BẮT ĐẦU IMPORT DỮ LIỆU VÀO CÁC BẢNG")
    print("-" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    total_imported = 0
    total_errors = 0
    table_stats = {}
    
    for name in ORDERED_COLLECTIONS:
        if name in EXCLUDED_TABLES:
            continue
        
        items = payload.get(name) or []
        if not isinstance(items, list) or not items:
            print(f"⏭️  Bảng '{name}': Bỏ qua (không có dữ liệu)")
            continue
        
        imported_count = 0
        error_count = 0
        
        print(f"\n📋 Đang import bảng '{name}'... ({len(items)} records)")
        
        keys = PRIMARY_KEYS.get(name) or []
        for idx, item in enumerate(items, 1):
            cols = list(item.keys())
            placeholders = ','.join(['?'] * len(cols))
            values = [item.get(c) for c in cols]
            
            try:
                cur.execute(f"INSERT OR REPLACE INTO {name} ({','.join(cols)}) VALUES ({placeholders})", values)
                imported_count += 1
                if idx % 50 == 0:
                    print(f"   ⏳ Đã import {idx}/{len(items)} records...", end='\r')
            except Exception as e:
                error_count += 1
                if error_count <= 3:  # Chỉ hiển thị 3 lỗi đầu tiên
                    print(f"\n   ⚠️  Lỗi ở record {idx}: {str(e)[:100]}")
        
        table_stats[name] = {
            'imported': imported_count,
            'errors': error_count,
            'total': len(items)
        }
        
        total_imported += imported_count
        total_errors += error_count
        
        status_icon = "✅" if error_count == 0 else "⚠️"
        print(f"   {status_icon} Hoàn thành: {imported_count}/{len(items)} records imported, {error_count} lỗi")
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print("📈 TỔNG KẾT IMPORT")
    print("=" * 60)
    print(f"✅ Tổng số records đã import: {total_imported}")
    if total_errors > 0:
        print(f"⚠️  Tổng số lỗi: {total_errors}")
    print()
    print("📊 Chi tiết theo bảng:")
    for table_name, stats in table_stats.items():
        status = "✅" if stats['errors'] == 0 else "⚠️"
        print(f"   {status} {table_name}: {stats['imported']}/{stats['total']} records")
        if stats['errors'] > 0:
            print(f"      ⚠️  {stats['errors']} lỗi")
    print()
    print("=" * 60)
    print("✅ HOÀN THÀNH IMPORT DỮ LIỆU")
    print("=" * 60)
    
    result = {
        "ok": True,
        "input": INPUT_PATH,
        "db": DB_PATH,
        "stats": {
            "total_imported": total_imported,
            "total_errors": total_errors,
            "tables": table_stats
        }
    }
    print()
    print("📄 JSON Output:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return 0 if total_errors == 0 else 1

if __name__ == '__main__':
    sys.exit(import_data())

