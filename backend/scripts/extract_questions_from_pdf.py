import os
import sys
import json
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

try:
    import pdfplumber
except ImportError:
    print("❌ Cần cài đặt pdfplumber: pip install pdfplumber")
    sys.exit(1)

# Sử dụng cùng cấu trúc với export_to_data_json.py
BASE_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.dirname(BASE_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'backend', 'db.sqlite')
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'data.json')

# Import INCLUDE_TABLES từ export_to_data_json.py
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

# Patterns để nhận diện câu hỏi và đáp án
QUESTION_PATTERNS = [
    r'^Câu\s*(\d+)[\.\):]\s*(.+?)(?=Câu\s*\d+|$)',  # Câu 1. hoặc Câu 1)
    r'^(\d+)[\.\)]\s*(.+?)(?=^\d+[\.\)]|$)',  # 1. hoặc 1)
    r'^Question\s*(\d+)[\.\):]\s*(.+?)(?=Question\s*\d+|$)',  # Question 1.
]

OPTION_PATTERNS = [
    r'^[A-D][\.\)]\s*(.+?)(?=^[A-D][\.\)]|$)',  # A. B. C. D. (multi-line)
    r'^[A-D][\.\)]\s*(.+?)(?=\n|$)',  # A. (single line)
    r'\b([A-D])[\.\)]\s*([^A-D\.\)]+?)(?=\s+[A-D][\.\)]|$)',  # A. text B. text (same line)
]

CORRECT_ANSWER_PATTERNS = [
    r'Đáp án[:\s]+([A-D])',
    r'Đáp án đúng[:\s]+([A-D])',
    r'Answer[:\s]+([A-D])',
    r'Correct[:\s]+([A-D])',
]


def extract_text_from_pdf(pdf_path: str) -> str:
    """Trích xuất text từ file PDF"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Không tìm thấy file: {pdf_path}")
    
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise Exception(f"Lỗi khi đọc PDF: {str(e)}")
    
    return text


def parse_questions(text: str) -> List[Dict]:
    """Parse text để tìm các câu hỏi"""
    questions = []
    
    # Tách text thành các dòng
    lines = text.split('\n')
    full_text = '\n'.join(lines)
    
    # Tìm tất cả các câu hỏi
    question_matches = []
    for pattern in QUESTION_PATTERNS:
        matches = re.finditer(pattern, full_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        for match in matches:
            question_num = match.group(1)
            question_content = match.group(2).strip()
            question_matches.append({
                'number': int(question_num),
                'content': question_content,
                'start': match.start(),
                'end': match.end()
            })
    
    # Sắp xếp theo vị trí trong text
    question_matches.sort(key=lambda x: x['start'])
    
    # Parse từng câu hỏi
    for i, q_match in enumerate(question_matches):
        question_text = q_match['content']
        question_num = q_match['number']
        
        # Tìm phần đáp án (từ vị trí hiện tại đến câu hỏi tiếp theo)
        next_start = question_matches[i + 1]['start'] if i + 1 < len(question_matches) else len(full_text)
        question_section = full_text[q_match['start']:next_start]
        
        # Tìm các lựa chọn A, B, C, D
        options = []
        option_texts = {}
        
        # Pattern 1: Tìm options trên nhiều dòng (A.\n...\nB.\n...)
        for option_pattern in OPTION_PATTERNS[:2]:  # 2 patterns đầu
            option_matches = re.finditer(option_pattern, question_section, re.MULTILINE)
            for opt_match in option_matches:
                option_letter = opt_match.group(0)[0].upper()
                option_content = opt_match.group(1).strip()
                if option_letter in ['A', 'B', 'C', 'D']:
                    option_texts[option_letter] = option_content
        
        # Pattern 2: Tìm tất cả các vị trí có "A.", "B.", "C.", "D." trong section
        # Để tách chính xác các options, đặc biệt khi chúng nằm trên cùng dòng
        option_positions = []
        found_letters = set()  # Để tránh lấy trùng option của cùng một chữ cái
        
        for letter in ['A', 'B', 'C', 'D']:
            # Tìm tất cả các vị trí có pattern "A. " hoặc "A) " trong section
            pattern = rf'\b{letter}[\.\)]\s+'
            for match in re.finditer(pattern, question_section, re.IGNORECASE):
                start_pos = match.end()  # Vị trí bắt đầu nội dung option
                match_start = match.start()
                
                # Chỉ lấy option đầu tiên của mỗi chữ cái (tránh trùng)
                # Hoặc nếu chưa có option nào của chữ cái này
                if letter.upper() not in found_letters:
                    option_positions.append({
                        'letter': letter.upper(),
                        'start': start_pos,
                        'match_start': match_start
                    })
                    found_letters.add(letter.upper())
                else:
                    # Nếu đã có option của chữ cái này, kiểm tra xem option mới có gần hơn không
                    # (có thể có trường hợp option xuất hiện nhiều lần)
                    existing = next((p for p in option_positions if p['letter'] == letter.upper()), None)
                    if existing and match_start < existing['match_start']:
                        # Option mới gần hơn, thay thế
                        option_positions.remove(existing)
                        option_positions.append({
                            'letter': letter.upper(),
                            'start': start_pos,
                            'match_start': match_start
                        })
        
        # Sắp xếp theo vị trí
        option_positions.sort(key=lambda x: x['start'])
        
        # Tách nội dung từng option dựa trên vị trí
        for i, pos in enumerate(option_positions):
            letter = pos['letter']
            start_pos = pos['start']
            
            # Tìm vị trí kết thúc: option tiếp theo hoặc cuối section
            if i + 1 < len(option_positions):
                # Có option tiếp theo
                end_pos = option_positions[i + 1]['match_start']  # Bắt đầu từ chữ cái của option tiếp theo
            else:
                # Option cuối cùng - tìm đến câu hỏi tiếp theo hoặc cuối section
                # Tìm pattern "Câu X" hoặc số tiếp theo để xác định ranh giới
                next_question_match = re.search(r'Câu\s+\d+|^\d+[\.\)]', question_section[start_pos:], re.MULTILINE)
                if next_question_match:
                    end_pos = start_pos + next_question_match.start()
                else:
                    end_pos = len(question_section)
            
            # Lấy nội dung option
            content = question_section[start_pos:end_pos].strip()
            
            # Loại bỏ các ký tự đặc biệt và làm sạch
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Loại bỏ dấu chấm cuối nếu có (nhưng giữ lại nếu là phần của câu)
            # Chỉ loại bỏ nếu dấu chấm đứng một mình ở cuối
            if content.endswith('.') and len(content) > 1:
                # Kiểm tra xem có phải là dấu chấm kết thúc câu không
                if not content.endswith('..'):
                    # Loại bỏ dấu chấm cuối nếu không phải là dấu chấm trong HTML tag hoặc số
                    if not re.search(r'<\w+>.*\.$', content):  # Không phải HTML tag
                        content = content.rstrip('. ')
            
            # Chỉ lưu nếu có nội dung và đủ dài
            if content and len(content) > 1:
                # Chỉ cập nhật nếu chưa có (đã kiểm tra ở trên)
                if letter not in option_texts:
                    option_texts[letter] = content
        
        # Pattern 3: Fallback - Tìm options trên từng dòng riêng biệt (nếu chưa đủ 4 options)
        if len(option_texts) < 4:
            lines = question_section.split('\n')
            for line in lines:
                # Tìm pattern: A. text (trên một dòng riêng)
                single_option_pattern = r'^([A-D])[\.\)]\s+(.+?)$'
                match = re.match(single_option_pattern, line.strip(), re.IGNORECASE)
                if match:
                    letter = match.group(1).upper()
                    content = match.group(2).strip()
                    content = re.sub(r'\s+', ' ', content).strip()
                    if letter in ['A', 'B', 'C', 'D'] and content and len(content) > 1:
                        if letter not in option_texts:
                            option_texts[letter] = content
        
        # Sắp xếp options theo thứ tự A, B, C, D
        sorted_options = []
        for letter in ['A', 'B', 'C', 'D']:
            if letter in option_texts:
                sorted_options.append({
                    'option_text': option_texts[letter],
                    'is_correct': False  # Sẽ được cập nhật sau
                })
        
        # Tìm đáp án đúng
        correct_answer = None
        for pattern in CORRECT_ANSWER_PATTERNS:
            match = re.search(pattern, question_section, re.IGNORECASE)
            if match:
                correct_answer = match.group(1).upper()
                break
        
        # Nếu không tìm thấy đáp án trong section này, tìm trong toàn bộ text
        if not correct_answer:
            # Tìm phần đáp án ở cuối file (tăng lên 5000 ký tự)
            answer_section = full_text[-5000:]  # 5000 ký tự cuối
            
            # Pattern mới: Tìm bảng đáp án dạng "Câu 1: A" hoặc "1. A" hoặc "1 A"
            answer_table_patterns = [
                rf'[Cc]âu\s*{question_num}[:\s]+([A-D])',
                rf'^{question_num}[\.\):\s]+([A-D])',
                rf'\b{question_num}\s+([A-D])\b',
            ]
            
            for pattern in answer_table_patterns:
                match = re.search(pattern, answer_section, re.MULTILINE | re.IGNORECASE)
                if match:
                    correct_answer = match.group(1).upper()
                    break
            
            # Nếu vẫn chưa tìm thấy, thử các pattern cũ
            if not correct_answer:
                for pattern in CORRECT_ANSWER_PATTERNS:
                    match = re.search(pattern, answer_section, re.IGNORECASE)
                    if match:
                        # Kiểm tra xem có phải đáp án của câu này không
                        answer_text = match.group(0)
                        if str(question_num) in answer_text or re.search(rf'câu\s*{question_num}', answer_text, re.IGNORECASE):
                            correct_answer = match.group(1).upper()
                            break
        
        # Đánh dấu đáp án đúng
        if correct_answer and sorted_options:
            option_index = ord(correct_answer) - ord('A')
            if 0 <= option_index < len(sorted_options):
                sorted_options[option_index]['is_correct'] = True
        
        # Xác định loại câu hỏi
        question_type = 'multiple_choice'
        if len(sorted_options) == 2:
            # Kiểm tra xem có phải True/False không
            option_texts_lower = [opt['option_text'].lower() for opt in sorted_options]
            if any('đúng' in txt or 'sai' in txt or 'true' in txt or 'false' in txt for txt in option_texts_lower):
                question_type = 'true_false'
        elif len(sorted_options) == 0:
            question_type = 'short_answer'
        
        # Làm sạch question_text (loại bỏ phần options nếu có)
        clean_question_text = question_text
        for letter in ['A', 'B', 'C', 'D']:
            # Loại bỏ pattern như "A. ..." khỏi question_text
            clean_question_text = re.sub(rf'^{letter}[\.\)]\s*.+?$', '', clean_question_text, flags=re.MULTILINE)
        
        clean_question_text = re.sub(r'\s+', ' ', clean_question_text).strip()
        
        question_data = {
            'question_text': clean_question_text or question_text.strip(),
            'question_type': question_type,
            'points': 1.0,
            'options': sorted_options,
            'correct_answer': correct_answer
        }
        
        questions.append(question_data)
    
    return questions


def load_existing_data(data_path: str) -> Dict:
    """Load dữ liệu hiện có từ data.json (nếu có)"""
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None


def export_to_json(questions: List[Dict], pdf_path: str, output_path: str = None, merge_with_existing: bool = True):
    """Xuất câu hỏi ra file JSON theo format của export_to_data_json.py"""
    if output_path is None:
        output_path = OUTPUT_PATH
    
    # Load dữ liệu hiện có nếu muốn merge
    existing_data = None
    if merge_with_existing:
        existing_data = load_existing_data(output_path)
    
    # Tạo data structure giống export_to_data_json.py
    if existing_data:
        data = existing_data.copy()
        # Cập nhật metadata
        data["metadata"] = {
            "source": "sqlite_and_pdf",
            "pdf_source_file": pdf_path,
            "schema_version": "2024-11",
            "generated_at": datetime.now().isoformat(timespec='seconds'),
            "pdf_extracted_questions": len(questions)
        }
    else:
        # Tạo mới với format giống export_to_data_json.py
        data = {
            "metadata": {
                "source": "pdf_extraction",
                "pdf_source_file": pdf_path,
                "schema_version": "2024-11",
                "generated_at": datetime.now().isoformat(timespec='seconds'),
                "pdf_extracted_questions": len(questions)
            }
        }
        # Khởi tạo tất cả các tables
        for table_name in INCLUDE_TABLES:
            data[table_name] = []
    
    # Lấy ID tiếp theo cho questions (tránh trùng)
    existing_question_ids = [q.get('question_id', 0) for q in data.get('questions', [])]
    next_question_id = max(existing_question_ids) + 1 if existing_question_ids else 1
    
    existing_option_ids = [o.get('option_id', 0) for o in data.get('question_options', [])]
    next_option_id = max(existing_option_ids) + 1 if existing_option_ids else 1
    
    existing_answer_ids = [a.get('answer_id', 0) for a in data.get('question_answers', [])]
    next_answer_id = max(existing_answer_ids) + 1 if existing_answer_ids else 1
    
    # Thêm questions mới vào data
    for q in questions:
        # Thêm vào questions
        question_record = {
            "question_id": next_question_id,
            "exam_id": None,  # Có thể set sau
            "question_text": q["question_text"],
            "question_type": q["question_type"],
            "points": q.get("points", 1.0),
            "created_at": datetime.now().isoformat(timespec='seconds')
        }
        data["questions"].append(question_record)
        
        # Thêm options nếu là multiple_choice hoặc true_false
        if q["question_type"] in ["multiple_choice", "true_false"] and q.get("options"):
            for option in q["options"]:
                option_record = {
                    "option_id": next_option_id,
                    "question_id": next_question_id,
                    "option_text": option["option_text"],
                    "is_correct": 1 if option.get("is_correct") else 0
                }
                data["question_options"].append(option_record)
                next_option_id += 1
        
        # Thêm correct_answer
        if q.get("correct_answer"):
            answer_record = {
                "answer_id": next_answer_id,
                "question_id": next_question_id,
                "correct_answer": q["correct_answer"]
            }
            data["question_answers"].append(answer_record)
            next_answer_id += 1
        
        next_question_id += 1
    
    # Ghi ra file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return output_path


def extract(pdf_path: str, output_path: str = None, merge: bool = True, import_to_db: bool = False):
    """Hàm chính để trích xuất câu hỏi từ PDF và xuất ra JSON (format giống export_to_data_json.py)"""
    try:
        print("=" * 60)
        print("🚀 BẮT ĐẦU TRÍCH XUẤT CÂU HỎI TỪ PDF")
        print("=" * 60)
        print(f"📄 File PDF: {pdf_path}")
        if output_path:
            print(f"📄 Output file: {output_path}")
        else:
            print(f"📄 Output file: {OUTPUT_PATH} (mặc định - giống export_to_data_json.py)")
        
        # Trích xuất text từ PDF
        print("\n📖 Đang đọc PDF...")
        text = extract_text_from_pdf(pdf_path)
        print(f"✅ Đã đọc {len(text)} ký tự từ PDF")
        
        # Parse câu hỏi
        print("\n🔍 Đang phân tích và trích xuất câu hỏi...")
        questions = parse_questions(text)
        print(f"✅ Đã tìm thấy {len(questions)} câu hỏi")
        
        if len(questions) == 0:
            print("⚠️  Không tìm thấy câu hỏi nào. Có thể format PDF không đúng.")
            print("\n💡 Gợi ý:")
            print("   - Đảm bảo câu hỏi bắt đầu bằng 'Câu 1.', '1.', hoặc 'Question 1.'")
            print("   - Đảm bảo đáp án có format A. B. C. D.")
            print("   - Kiểm tra xem PDF có phải là text-based (không phải scanned image)")
            return 1
        
        # Xuất ra JSON (format giống export_to_data_json.py)
        print("\n💾 Đang xuất ra file JSON (format giống export_to_data_json.py)...")
        if merge:
            print("   ℹ️  Đang merge với dữ liệu hiện có (nếu có)...")
        output_file = export_to_json(questions, pdf_path, output_path, merge_with_existing=merge)
        print(f"✅ Đã xuất ra file: {output_file}")
        
        # Import vào database nếu được yêu cầu
        if import_to_db and os.path.exists(DB_PATH):
            print("\n💾 Đang import vào database...")
            try:
                # Sử dụng logic tương tự import_from_data_json.py
                with open(output_file, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
                
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                
                imported_count = 0
                for q in payload.get('questions', []):
                    try:
                        cur.execute("""
                            INSERT OR REPLACE INTO questions 
                            (question_id, exam_id, question_text, question_type, points, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            q.get('question_id'),
                            q.get('exam_id'),
                            q.get('question_text'),
                            q.get('question_type'),
                            q.get('points', 1.0),
                            q.get('created_at')
                        ))
                        imported_count += 1
                    except Exception as e:
                        print(f"   ⚠️  Lỗi khi import question {q.get('question_id')}: {str(e)[:50]}")
                
                for opt in payload.get('question_options', []):
                    try:
                        cur.execute("""
                            INSERT OR REPLACE INTO question_options 
                            (option_id, question_id, option_text, is_correct)
                            VALUES (?, ?, ?, ?)
                        """, (
                            opt.get('option_id'),
                            opt.get('question_id'),
                            opt.get('option_text'),
                            opt.get('is_correct', 0)
                        ))
                    except Exception as e:
                        print(f"   ⚠️  Lỗi khi import option {opt.get('option_id')}: {str(e)[:50]}")
                
                for ans in payload.get('question_answers', []):
                    try:
                        cur.execute("""
                            INSERT OR REPLACE INTO question_answers 
                            (answer_id, question_id, correct_answer)
                            VALUES (?, ?, ?)
                        """, (
                            ans.get('answer_id'),
                            ans.get('question_id'),
                            ans.get('correct_answer')
                        ))
                    except Exception as e:
                        print(f"   ⚠️  Lỗi khi import answer {ans.get('answer_id')}: {str(e)[:50]}")
                
                conn.commit()
                conn.close()
                print(f"✅ Đã import {imported_count} câu hỏi vào database")
            except Exception as e:
                print(f"⚠️  Lỗi khi import vào database: {str(e)}")
        
        print("\n" + "=" * 60)
        print("📊 TỔNG KẾT")
        print("=" * 60)
        print(f"✅ Tổng số câu hỏi đã trích xuất: {len(questions)}")
        
        # Thống kê theo loại
        type_stats = {}
        for q in questions:
            q_type = q.get("question_type", "unknown")
            type_stats[q_type] = type_stats.get(q_type, 0) + 1
        
        print("\n📈 Thống kê theo loại:")
        for q_type, count in type_stats.items():
            print(f"   - {q_type}: {count} câu")
        
        print("\n" + "=" * 60)
        print("✅ HOÀN THÀNH")
        print("=" * 60)
        print(f"\n💡 Tip: Bạn có thể chạy export_to_data_json.py để export toàn bộ database ra JSON")
        
        result = {
            "ok": True,
            "pdf_path": pdf_path,
            "output_path": output_file,
            "total_questions": len(questions),
            "stats": type_stats,
            "format": "compatible_with_export_to_data_json"
        }
        
        print("\n📄 JSON Output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ LỖI: {str(e)}")
        print(json.dumps({"ok": False, "error": "file_not_found", "path": pdf_path}))
        return 1
    except Exception as e:
        print(f"❌ LỖI: {str(e)}")
        print(json.dumps({"ok": False, "error": str(e)}))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("❌ Cách sử dụng: python extract_questions_from_pdf.py <path_to_pdf> [options]")
        print("\nOptions:")
        print("   [output_json_path]  - Đường dẫn file JSON output (mặc định: data.json)")
        print("   --no-merge          - Không merge với data.json hiện có")
        print("   --import-db         - Import trực tiếp vào database sau khi extract")
        print("\nVí dụ:")
        print("   python extract_questions_from_pdf.py exam.pdf")
        print("   python extract_questions_from_pdf.py exam.pdf output.json")
        print("   python extract_questions_from_pdf.py exam.pdf --no-merge")
        print("   python extract_questions_from_pdf.py exam.pdf --import-db")
        print("   python extract_questions_from_pdf.py exam.pdf data.json --import-db")
        print("\n💡 Lưu ý: File output mặc định là data.json (giống export_to_data_json.py)")
        print("   Bạn có thể chạy export_to_data_json.py sau đó để export toàn bộ database")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = None
    merge = True
    import_to_db = False
    
    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == '--no-merge':
            merge = False
        elif arg == '--import-db':
            import_to_db = True
        elif not arg.startswith('--'):
            output_path = arg
    
    sys.exit(extract(pdf_path, output_path, merge=merge, import_to_db=import_to_db))

