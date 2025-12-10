from google import genai
from google.genai import types
import os
import time
import json
from typing import Optional, Dict, Any
from backend.config import settings

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "rag", "uploads")
PERSISTENCE_FILE = os.path.join(os.path.dirname(__file__), "..", "rag", "store_state.json")
ALLOWED_EXTENSIONS = {"txt", "pdf", "doc", "docx", "json", "md", "py", "js", "html", "css", "xml", "csv", "png", "jpg", "jpeg", "gif", "webp", "bmp"}
MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_HISTORY = 10

# Education-focused system prompts
EDUCATION_PROMPTS = {
    "Hỏi đáp tấn công và phòng thủ mạng": """Bạn là một Chuyên gia An ninh mạng cấp cao (Senior Cybersecurity Expert) với tư duy "White Hat". Nhiệm vụ của bạn là giải đáp các thắc mắc về kỹ thuật tấn công và phòng thủ.

    HƯỚNG DẪN TRẢ LỜI:
    1.  **Phân tích chuyên sâu:** Giải thích cơ chế hoạt động của lỗ hổng hoặc kỹ thuật tấn công từ gốc rễ (Root cause), sau đó đi vào chi tiết kỹ thuật.
    2.  **Ngôn ngữ:** Sử dụng thuật ngữ chuyên ngành chính xác, nhưng kèm theo giải thích hoặc so sánh ẩn dụ để dễ hiểu.
    3.  **Cấu trúc câu trả lời:**
        *   **Khái niệm:** Định nghĩa ngắn gọn.
        *   **Cơ chế:** Cách thức tấn công/lỗ hổng hoạt động (Technical breakdown).
        *   **Ví dụ thực tế:** Phân tích các vụ việc đã xảy ra (Case studies) hoặc kịch bản giả định.
        *   **Phòng thủ & Khắc phục:** Các biện pháp giảm thiểu rủi ro (Mitigation) và vá lỗi (Patching).
    4.  **An toàn & Đạo đức:**
        *   Bắt buộc phải có tuyên bố miễn trừ trách nhiệm (Disclaimer) trước khi đi vào chi tiết kỹ thuật nhạy cảm.
        *   Chỉ cung cấp kiến thức để phòng thủ và nghiên cứu, TUYỆT ĐỐI KHÔNG cung cấp mã khai thác (exploit code) sẵn dùng cho mục đích xấu hoặc hướng dẫn tấn công vào mục tiêu cụ thể không được phép.
        *   Cảnh báo rõ ràng về các quy định pháp luật (Luật An ninh mạng) liên quan.

    Hãy trả lời bằng tiếng Việt, giọng văn chuyên nghiệp, khách quan và nghiêm túc.""",

    "Đào tạo mạng": """Bạn là một Giáo viên An ninh mạng tâm huyết, có phương pháp sư phạm xuất sắc. Đối tượng của bạn là học sinh/sinh viên đang bắt đầu tìm hiểu.

    HƯỚNG DẪN GIẢNG DẠY:
    1.  **Phương pháp tiếp cận:** Đi từ đơn giản đến phức tạp. Sử dụng các hình ảnh so sánh đời thường (Analogies) để giải thích các khái niệm trừu tượng (TCP/IP, Encryption, Firewall...).
    2.  **Tư duy phòng thủ:** Luôn giải thích "tại sao cần bảo mật" trước khi giải thích "làm thế nào để bảo mật".
    3.  **Thực hành an toàn:**
        *   Đề xuất các bài tập có thể thực hiện trong môi trường Lab (máy ảo, Packet Tracer, CTF platforms).
        *   Tuyệt đối không khuyến khích thử nghiệm trên hệ thống thật khi chưa được phép.
    4.  **Định hướng nghề nghiệp:**
        *   Lồng ghép các bài học về đạo đức nghề nghiệp (Ethical Hacking) vào từng chủ đề.
        *   Giới thiệu các chứng chỉ hoặc lộ trình học tập liên quan.
    5.  **Tương tác:** Luôn khích lệ, dùng ngôn ngữ tích cực. Đặt câu hỏi ngược lại để gợi mở tư duy cho học sinh.

    Hãy trả lời bằng tiếng Việt. Mục tiêu là giúp học sinh không chỉ hiểu kiến thức mà còn yêu thích và tôn trọng nghề nghiệp này.""",

    "Tạo câu hỏi ôn tập": """Bạn là một Giảng viên An ninh mạng đang biên soạn ngân hàng đề thi chất lượng cao.

    YÊU CẦU TẠO CÂU HỎI:
    1.  **Đa dạng hình thức:** Tạo ra các câu hỏi trắc nghiệm (Multiple Choice), Tự luận ngắn (Short Answer), hoặc Tình huống (Scenario-based).
    2.  **Tư duy phản biện:** Câu hỏi không chỉ kiểm tra trí nhớ (nhớ cổng, nhớ lệnh) mà phải kiểm tra khả năng phân tích và xử lý sự cố.
    3.  **Cấu trúc đầu ra:**
        *   **Câu hỏi:** Rõ ràng, không gây nhầm lẫn.
        *   **Mức độ:** Ghi rõ (Dễ/Trung bình/Khó).
        *   **Đáp án đúng:** Chính xác về mặt kỹ thuật.
        *   **Giải thích chi tiết:**
            *   Tại sao đáp án này đúng? (Giải thích cơ chế).
            *   Tại sao các đáp án khác sai? (Phân tích các bẫy/distractors).
    4.  **Tính thực tế:** Ưu tiên các câu hỏi dựa trên các kịch bản tấn công/phòng thủ thực tế trong môi trường doanh nghiệp.

    Hãy trả lời bằng tiếng Việt. Đảm bảo câu hỏi giúp người học củng cố kiến thức vững chắc.""",
}

class GeminiRAGService:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or settings.GEMINI_API_KEY
        self.enabled = bool(key)
        self.client = genai.Client(api_key=key) if self.enabled else None
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        self.conversation_history = []
        self.file_search_store = None
        self.uploaded_files = []
        self._load_state()

    def _load_state(self):
        try:
            if os.path.exists(PERSISTENCE_FILE):
                with open(PERSISTENCE_FILE, "r") as f:
                    state = json.load(f)
                store_name = state.get("store_name")
                self.uploaded_files = state.get("uploaded_files", [])
                
                # Restore store connection if store_name exists
                if store_name and self.enabled:
                    try:
                        self.file_search_store = self.client.file_search_stores.get(name=store_name)
                        print(f"[RAG] Successfully restored store: {store_name}")
                    except Exception as e:
                        # Store might have been deleted, reset
                        print(f"[RAG] Failed to restore store {store_name}: {e}")
                        self.file_search_store = None
                        self.uploaded_files = []
        except Exception as e:
            print(f"[RAG] Error loading state: {e}")

    def _save_state(self):
        try:
            state = {
                "store_name": self.file_search_store.name if self.file_search_store else None,
                "uploaded_files": self.uploaded_files,
            }
            with open(PERSISTENCE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def _allowed_file(self, filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def upload(self, tmp_path: str, filename: str, metadata_json: str = "{}", chunking_json: str = "{}") -> Dict[str, Any]:
        if len(self.uploaded_files) >= 5:
            return {"error": "limit_reached"}
        if not self._allowed_file(filename):
            return {"error": "File type not supported"}
        file_size = os.path.getsize(tmp_path)
        try:
            custom_metadata = json.loads(metadata_json or "{}")
        except Exception:
            custom_metadata = {}
        if not custom_metadata:
            custom_metadata = {"source": "local", "subject": "General"}
        try:
            chunking_config = json.loads(chunking_json or "{}")
        except Exception:
            chunking_config = {}
        if not chunking_config:
            chunking_config = {"enabled": True, "max_tokens_per_chunk": 200, "max_overlap_tokens": 20}
        uploaded_api_file = None
        try:
            if not self.enabled:
                file_info = {
                    "filename": filename,
                    "size": file_size,
                    "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "custom_metadata": custom_metadata,
                    "chunking_config": chunking_config,
                    "file_api_name": None,
                    "document_id": None,
                }
                self.uploaded_files.append(file_info)
                self._save_state()
                return {
                    "success": True,
                    "filename": filename,
                    "file_size": file_size,
                    "store_name": None,
                    "document_id": None,
                    "uploaded_files": self.uploaded_files,
                }
            if self.file_search_store is None:
                self.file_search_store = self.client.file_search_stores.create(config={"display_name": "RAG-App-Store"})
            uploaded_api_file = self.client.files.upload(file=tmp_path, config={"display_name": filename})
            import_config: Dict[str, Any] = {}
            if custom_metadata:
                metadata_list = []
                for key, value in custom_metadata.items():
                    if isinstance(value, (int, float)):
                        metadata_list.append({"key": key, "numeric_value": value})
                    else:
                        metadata_list.append({"key": key, "string_value": str(value)})
                import_config["custom_metadata"] = metadata_list
            if chunking_config and chunking_config.get("enabled"):
                import_config["chunking_config"] = {
                    "white_space_config": {
                        "max_tokens_per_chunk": chunking_config.get("max_tokens_per_chunk", 200),
                        "max_overlap_tokens": chunking_config.get("max_overlap_tokens", 20),
                    }
                }
            operation = self.client.file_search_stores.import_file(
                file_search_store_name=self.file_search_store.name,
                file_name=uploaded_api_file.name,
                config=import_config if import_config else None,
            )
            max_wait = 120
            wait_time = 0
            while not operation.done and wait_time < max_wait:
                time.sleep(3)
                operation = self.client.operations.get(operation)
                wait_time += 3
            if not operation.done:
                return {"error": f"File processing timeout after {max_wait} seconds"}
            document_id = None
            if hasattr(operation, "response") and operation.response:
                document_id = getattr(operation.response, "name", None)
            file_info = {
                "filename": filename,
                "size": file_size,
                "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "custom_metadata": custom_metadata,
                "chunking_config": chunking_config if chunking_config.get("enabled") else None,
                "file_api_name": uploaded_api_file.name,
                "document_id": document_id,
            }
            self.uploaded_files.append(file_info)
            self._save_state()
            return {
                "success": True,
                "filename": filename,
                "file_size": file_size,
                "store_name": self.file_search_store.name,
                "document_id": document_id,
                "uploaded_files": self.uploaded_files,
            }
        except Exception as e:
            try:
                if uploaded_api_file:
                    self.client.files.delete(uploaded_api_file.name)
            except Exception:
                pass
            return {"error": f"Error uploading file: {str(e)}"}

    def chat(self, message: str, metadata_filter: str = "", system_prompt: str = "") -> Dict[str, Any]:
        if not message:
            return {"error": "No message provided"}
        if not self.enabled:
            assistant_message = "RAG chưa cấu hình. Vui lòng kiểm tra GEMINI_API_KEY trong biến môi trường."
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            if len(self.conversation_history) > MAX_HISTORY * 2:
                self.conversation_history = self.conversation_history[-MAX_HISTORY * 2:]
            return {"success": True, "response": assistant_message, "metadata": None, "conversation_length": len(self.conversation_history), "metadata_filter_used": None}
        
        # Store user message
        self.conversation_history.append({"role": "user", "content": message})
        context_messages = self.conversation_history[-MAX_HISTORY * 2:]
        
        # Build prompt with education context
        parts = []
        
        # Add system prompt if provided, or use default education prompt
        if system_prompt and system_prompt in EDUCATION_PROMPTS:
            parts.append(EDUCATION_PROMPTS[system_prompt])
        elif system_prompt:
            parts.append(f"System Instructions: {system_prompt}")
        else:
            # Default education prompt
            parts.append(EDUCATION_PROMPTS["Trả lời dựa trên tài liệu"])
        
        parts.append("\n---\n")
        
        # Add conversation context
        for msg in context_messages[:-1]:
            if msg["role"] == "user":
                parts.append(f"Học sinh: {msg['content']}")
            else:
                parts.append(f"Giáo viên: {msg['content']}")
        
        # Add current question
        parts.append(f"\nHọc sinh: {message}")
        parts.append("\nGiáo viên:")
        
        full_prompt = "\n\n".join(parts)
        
        # Use file search if store exists
        config_kwargs = {}
        if self.file_search_store is not None:
            file_search_config = types.FileSearch(file_search_store_names=[self.file_search_store.name])
            if metadata_filter:
                file_search_config.metadata_filter = metadata_filter
            config_kwargs["tools"] = [types.Tool(file_search=file_search_config)]
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
                config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None,
            )
            assistant_message = response.text
        except Exception as e:
            # Fallback: try without file search if error occurs
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{message}\n\nHãy trả lời bằng tiếng Việt và giải thích chi tiết.",
                )
                assistant_message = response.text + "\n\n(Lưu ý: Trả lời không sử dụng tài liệu vì có lỗi kỹ thuật)"
            except Exception as e2:
                return {"error": f"Lỗi khi gọi API: {str(e2)}"}
        
        # Store assistant response
        self.conversation_history.append({"role": "assistant", "content": assistant_message})
        if len(self.conversation_history) > MAX_HISTORY * 2:
            self.conversation_history = self.conversation_history[-MAX_HISTORY * 2:]
        
        # Extract grounding metadata (citations)
        metadata = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata") and candidate.grounding_metadata:
                grounding = candidate.grounding_metadata
                citations = []
                if hasattr(grounding, "grounding_chunks") and grounding.grounding_chunks:
                    for chunk in grounding.grounding_chunks:
                        if hasattr(chunk, "retrieved_context"):
                            ctx = chunk.retrieved_context
                            citation = {}
                            if hasattr(ctx, "title"):
                                citation["title"] = ctx.title
                            if hasattr(ctx, "uri"):
                                citation["uri"] = ctx.uri
                            if hasattr(ctx, "text"):
                                citation["text"] = ctx.text[:200] + "..." if len(ctx.text) > 200 else ctx.text
                            if citation:
                                citations.append(citation)
                if citations:
                    metadata = {"citations": citations, "citation_count": len(citations)}
        
        return {
            "success": True,
            "response": assistant_message,
            "metadata": metadata,
            "conversation_length": len(self.conversation_history),
            "metadata_filter_used": metadata_filter or None,
            "system_prompt_used": system_prompt or "Trả lời dựa trên tài liệu"
        }

    def delete_file(self, file_index: int) -> Dict[str, Any]:
        if file_index < 0 or file_index >= len(self.uploaded_files):
            return {"error": "Invalid file index"}
        info = self.uploaded_files[file_index]
        if info.get("file_api_name"):
            try:
                self.client.files.delete(info["file_api_name"])
            except Exception:
                pass
        deleted = self.uploaded_files.pop(file_index)
        self._save_state()
        return {"success": True, "message": f"File '{deleted['filename']}' deleted successfully", "uploaded_files": self.uploaded_files}

    def get_store_info(self) -> Dict[str, Any]:
        if self.file_search_store is None:
            return {"success": True, "store_exists": False, "message": "No file search store created yet"}
        details = self.client.file_search_stores.get(name=self.file_search_store.name)
        return {
            "success": True,
            "store_exists": True,
            "name": details.name,
            "display_name": getattr(details, "display_name", "N/A"),
            "create_time": getattr(details, "create_time", "N/A"),
            "update_time": getattr(details, "update_time", "N/A"),
            "document_count": len(self.uploaded_files),
        }

    def list_stores(self) -> Dict[str, Any]:
        stores = []
        for store in self.client.file_search_stores.list():
            stores.append({
                "name": store.name,
                "display_name": getattr(store, "display_name", "N/A"),
                "create_time": str(getattr(store, "create_time", "N/A")),
            })
        return {"success": True, "stores": stores, "count": len(stores)}

    def delete_store(self) -> Dict[str, Any]:
        if self.file_search_store is None:
            return {"error": "No store to delete"}
        name = self.file_search_store.name
        self.client.file_search_stores.delete(name=name, config={"force": True})
        self.file_search_store = None
        self.uploaded_files = []
        self._save_state()
        return {"success": True, "message": "File search store deleted successfully"}

    def clear_conversation(self) -> Dict[str, Any]:
        self.conversation_history = []
        return {"success": True, "message": "Conversation cleared"}

    def get_files(self) -> Dict[str, Any]:
        return {"success": True, "files": self.uploaded_files, "store_name": self.file_search_store.name if self.file_search_store else None}

    def status(self) -> Dict[str, Any]:
        return {
            "file_uploaded": self.file_search_store is not None,
            "conversation_length": len(self.conversation_history),
            "store_name": self.file_search_store.name if self.file_search_store else None,
            "uploaded_files": self.uploaded_files,
        }

    def api_info(self) -> Dict[str, Any]:
        metadata_keys = set()
        for info in self.uploaded_files:
            if info.get("custom_metadata"):
                for key in info["custom_metadata"].keys():
                    metadata_keys.add(key)
        return {
            "success": True,
            "api_key": settings.GEMINI_API_KEY,
            "store_exists": self.file_search_store is not None,
            "store_name": self.file_search_store.name if self.file_search_store else None,
            "store_display_name": getattr(self.file_search_store, "display_name", "RAG-App-Store") if self.file_search_store else "RAG-App-Store",
            "file_count": len(self.uploaded_files),
            "files": self.uploaded_files,
            "model": "gemini-2.5-flash",
            "metadata_keys": list(metadata_keys),
        }

    def update_api_key(self, new_api_key: str) -> Dict[str, Any]:
        if not new_api_key:
            return {"error": "API key cannot be empty"}
        self.client = genai.Client(api_key=new_api_key)
        return {"success": True, "message": "API key updated successfully"}
    
    def extract_questions_from_pdf(self, file_index: int) -> Dict[str, Any]:
        """Extract questions from an uploaded PDF file using Gemini Vision"""
        if file_index < 0 or file_index >= len(self.uploaded_files):
            return {"error": "Invalid file index"}
        
        file_info = self.uploaded_files[file_index]
        filename = file_info.get("filename", "")
        
        if not filename.lower().endswith(".pdf"):
            return {"error": "File is not a PDF"}
        
        if not self.enabled:
            return {"error": "RAG service not configured"}
        
        # Try to find the file in uploads folder
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return {"error": "PDF file not found in uploads folder"}
        
        try:
            # Use Gemini to analyze PDF and extract questions
            uploaded_file = self.client.files.upload(file=file_path)
            
            prompt = """Phân tích file PDF này và trích xuất TẤT CẢ các câu hỏi có trong đó.

Với mỗi câu hỏi, hãy trả về theo format JSON như sau:
{
  "questions": [
    {
      "question_number": 1,
      "question_text": "Nội dung câu hỏi",
      "question_type": "multiple_choice" hoặc "true_false" hoặc "short_answer",
      "options": [
        {"letter": "A", "text": "Đáp án A"},
        {"letter": "B", "text": "Đáp án B"},
        {"letter": "C", "text": "Đáp án C"},
        {"letter": "D", "text": "Đáp án D"}
      ],
      "correct_answer": "A" (nếu có)
    }
  ]
}

Lưu ý:
- Trích xuất CHÍNH XÁC nội dung câu hỏi và đáp án từ PDF
- Không thêm hoặc sửa đổi nội dung
- Nếu không tìm thấy đáp án đúng, bỏ qua trường "correct_answer"
- Chỉ trả về JSON, không có text khác

Bắt đầu phân tích:"""
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, uploaded_file],
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            try:
                questions_data = json.loads(response_text)
                questions = questions_data.get("questions", [])
                
                # Clean up uploaded file
                try:
                    self.client.files.delete(uploaded_file.name)
                except:
                    pass
                
                return {
                    "success": True,
                    "filename": filename,
                    "total_questions": len(questions),
                    "questions": questions
                }
            except json.JSONDecodeError as e:
                return {
                    "error": f"Failed to parse response as JSON: {str(e)}",
                    "raw_response": response_text[:500]
                }
                
        except Exception as e:
            return {"error": f"Failed to extract questions: {str(e)}"}
    
    def analyze_image(self, file_path: str, question: str = "") -> Dict[str, Any]:
        """Analyze an image file and answer questions about it"""
        if not self.enabled:
            return {"error": "RAG service not configured"}
        
        if not os.path.exists(file_path):
            return {"error": "Image file not found"}
        
        try:
            # Upload image to Gemini
            uploaded_file = self.client.files.upload(file=file_path)
            
            # Create prompt
            prompt = question if question else "Hãy mô tả chi tiết hình ảnh này và giải thích các nội dung liên quan đến học tập, giáo dục có trong hình."
            
            # Generate response
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, uploaded_file],
            )
            
            # Clean up
            try:
                self.client.files.delete(uploaded_file.name)
            except:
                pass
            
            return {
                "success": True,
                "response": response.text,
                "file_path": file_path
            }
        except Exception as e:
            return {"error": f"Failed to analyze image: {str(e)}"}
