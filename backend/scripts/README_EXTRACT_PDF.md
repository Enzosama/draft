# Hướng dẫn sử dụng Extract Questions from PDF

Script này cho phép trích xuất câu hỏi từ file PDF và xuất ra định dạng JSON **tương thích với `export_to_data_json.py`**.

## Tích hợp với export_to_data_json.py

- ✅ Sử dụng cùng constants và cấu trúc (`BASE_DIR`, `OUTPUT_PATH`, `INCLUDE_TABLES`)
- ✅ Xuất ra cùng format JSON với `export_to_data_json.py` (có `metadata` và tất cả các tables)
- ✅ Tự động merge với `data.json` hiện có (nếu có)
- ✅ Có thể import trực tiếp vào database
- ✅ Tương thích với `import_from_data_json.py`

## Cài đặt

1. Cài đặt thư viện cần thiết:
```bash
pip install pdfplumber
```

Hoặc thêm vào `requirements.txt`:
```
pdfplumber>=0.10.0
```

## Cách sử dụng

### Cú pháp cơ bản:
```bash
python backend/scripts/extract_questions_from_pdf.py <path_to_pdf> [options]
```

### Options:
- `[output_json_path]` - Đường dẫn file JSON output (mặc định: `data.json` - giống `export_to_data_json.py`)
- `--no-merge` - Không merge với `data.json` hiện có
- `--import-db` - Import trực tiếp vào database sau khi extract

### Ví dụ:
```bash
# Xuất ra file data.json (mặc định - giống export_to_data_json.py)
# Tự động merge với data.json hiện có nếu có
python backend/scripts/extract_questions_from_pdf.py exam.pdf

# Chỉ định file output khác
python backend/scripts/extract_questions_from_pdf.py exam.pdf my_questions.json

# Không merge với data.json hiện có
python backend/scripts/extract_questions_from_pdf.py exam.pdf --no-merge

# Import trực tiếp vào database sau khi extract
python backend/scripts/extract_questions_from_pdf.py exam.pdf --import-db

# Kết hợp các options
python backend/scripts/extract_questions_from_pdf.py exam.pdf output.json --import-db
```

### Workflow đề xuất:

1. **Extract từ PDF và merge với data hiện có:**
```bash
python backend/scripts/extract_questions_from_pdf.py exam.pdf
```

2. **Import vào database (nếu chưa dùng --import-db):**
```bash
python backend/scripts/import_from_data_json.py
```

3. **Export toàn bộ database ra JSON:**
```bash
python backend/scripts/export_to_data_json.py
```

## Format PDF được hỗ trợ

Script hỗ trợ các format câu hỏi sau:

### 1. Câu hỏi trắc nghiệm (Multiple Choice)
```
Câu 1. Nội dung câu hỏi?
A. Đáp án A
B. Đáp án B
C. Đáp án C
D. Đáp án D
Đáp án: C
```

Hoặc:
```
1. Nội dung câu hỏi?
A. Đáp án A
B. Đáp án B
C. Đáp án C
D. Đáp án D
```

### 2. Câu hỏi Đúng/Sai (True/False)
```
Câu 2. Nội dung câu hỏi?
A. Đúng
B. Sai
Đáp án: A
```

### 3. Câu hỏi tự luận (Short Answer)
```
Câu 3. Nội dung câu hỏi?
```

## Format Output JSON

File JSON được tạo ra có **cùng format với `export_to_data_json.py`**:

```json
{
  "metadata": {
    "source": "sqlite_and_pdf",
    "pdf_source_file": "exam.pdf",
    "schema_version": "2024-11",
    "generated_at": "2024-11-20T10:30:00",
    "pdf_extracted_questions": 10
  },
  "subjects": [],
  "posts": [],
  "exams": [],
  "questions": [
    {
      "question_id": 1,
      "exam_id": null,
      "question_text": "Nội dung câu hỏi?",
      "question_type": "multiple_choice",
      "points": 1.0,
      "created_at": "2024-11-20T10:30:00"
    }
  ],
  "question_options": [
    {
      "option_id": 1,
      "question_id": 1,
      "option_text": "Đáp án A",
      "is_correct": 0
    },
    {
      "option_id": 2,
      "question_id": 1,
      "option_text": "Đáp án B",
      "is_correct": 1
    }
  ],
  "question_answers": [
    {
      "answer_id": 1,
      "question_id": 1,
      "correct_answer": "B"
    }
  ],
  "exam_questions": [],
  "classrooms": [],
  ...
}
```

**Lưu ý:** Format này giống hệt với `export_to_data_json.py`, nên bạn có thể:
- Merge với `data.json` hiện có
- Import bằng `import_from_data_json.py`
- Export lại bằng `export_to_data_json.py` để có toàn bộ database

## Import vào Database

Có 2 cách:

1. **Tự động import khi extract (khuyến nghị):**
```bash
python backend/scripts/extract_questions_from_pdf.py exam.pdf --import-db
```

2. **Import sau bằng script:**
```bash
# Sau khi extract
python backend/scripts/extract_questions_from_pdf.py exam.pdf

# Import vào database
python backend/scripts/import_from_data_json.py
```

## Lưu ý

- PDF phải là text-based (không phải scanned image)
- Câu hỏi nên có format nhất quán
- Đáp án có thể nằm ở cuối file hoặc sau mỗi câu hỏi
- Script tự động nhận diện loại câu hỏi (multiple_choice, true_false, short_answer)

## Xử lý lỗi

Nếu không tìm thấy câu hỏi:
- Kiểm tra format PDF có đúng không
- Đảm bảo PDF là text-based
- Thử chỉnh sửa patterns trong script nếu format đặc biệt

