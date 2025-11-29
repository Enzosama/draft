from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Optional
import os
import shutil
from backend.services.rag_service import GeminiRAGService
from backend.config import settings
from backend.middleware.auth import get_current_user, get_current_user_optional
import httpx

router = APIRouter()

service: Optional[GeminiRAGService] = None

def _get_service() -> GeminiRAGService:
    global service
    if service is None:
        service = GeminiRAGService()
    # Check if store needs to be reloaded (for hot reload scenarios)
    elif service.file_search_store is None and service.enabled:
        import json
        import os
        persistence_file = os.path.join(os.path.dirname(__file__), "..", "rag", "store_state.json")
        if os.path.exists(persistence_file):
            try:
                with open(persistence_file, "r") as f:
                    state = json.load(f)
                store_name = state.get("store_name")
                if store_name:
                    # Store exists in file but not loaded, recreate service
                    service = GeminiRAGService()
            except Exception:
                pass
    return service

def _reset_service():
    """Force reset service - useful for reloading state"""
    global service
    service = None

def _uploads_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "rag", "uploads")

@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    chunking_config: Optional[str] = Form(None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    os.makedirs(_uploads_dir(), exist_ok=True)
    tmp_path = os.path.join(_uploads_dir(), file.filename)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    svc = _get_service()
    result = svc.upload(tmp_path, file.filename, metadata or "{}", chunking_config or "{}")
    # Keep file for later use (extract questions, etc.)
    # Don't delete immediately
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/import-url")
async def import_url(payload: dict):
    url = str(payload.get("url", "")).strip()
    filename = str(payload.get("filename", "")).strip()
    metadata = str(payload.get("metadata", ""))
    chunking_config = str(payload.get("chunking_config", ""))
    if not url:
        raise HTTPException(status_code=400, detail="invalid_url")
    svc = _get_service()
    files_state = svc.get_files()
    if isinstance(files_state, dict) and len(files_state.get("files", [])) >= 5:
        raise HTTPException(status_code=400, detail="limit_reached")
    tmp_dir = _uploads_dir()
    os.makedirs(tmp_dir, exist_ok=True)
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="download_failed")
        content_type = resp.headers.get("content-type", "").lower()
        ext = "txt"
        if "pdf" in content_type:
            ext = "pdf"
        elif "html" in content_type:
            ext = "html"
        elif "json" in content_type:
            ext = "json"
        elif "plain" in content_type:
            ext = "txt"
        base = filename or os.path.basename(url) or "document"
        if "." not in base:
            base = f"{base}.{ext}"
        tmp_path = os.path.join(tmp_dir, base)
        with open(tmp_path, "wb") as f:
            f.write(resp.content)
    result = svc.upload(tmp_path, base, metadata or "{}", chunking_config or "{}")
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/chat")
async def chat(
    payload: dict,
    user: Optional[dict] = Depends(get_current_user_optional),
):
    message = payload.get("message", "")
    metadata_filter = payload.get("metadata_filter", "")
    system_prompt = payload.get("system_prompt", "")
    svc = _get_service()
    result = svc.chat(message, metadata_filter, system_prompt)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.delete("/delete-file/{file_index}")
async def delete_file(file_index: int, user: Optional[dict] = Depends(get_current_user_optional)):
    """Delete a file - no auth required for ease of use"""
    svc = _get_service()
    result = svc.delete_file(file_index)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/store-info")
async def store_info():
    try:
        svc = _get_service()
        return svc.get_store_info()
    except Exception:
        return {"success": True, "store_exists": False, "name": None, "document_count": 0}

@router.get("/stores")
async def stores():
    svc = _get_service()
    return svc.list_stores()

@router.delete("/delete-store")
async def delete_store(user: Optional[dict] = Depends(get_current_user_optional)):
    """Delete entire store - no auth required for ease of use"""
    svc = _get_service()
    result = svc.delete_store()
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/clear")
async def clear():
    svc = _get_service()
    return svc.clear_conversation()

@router.post("/reload-service")
async def reload_service():
    """Force reload service to pick up latest state"""
    import json
    _reset_service()
    
    # Try to load manually to see what fails
    persistence_file = os.path.join(os.path.dirname(__file__), "..", "rag", "store_state.json")
    manual_load_error = None
    manual_store = None
    
    try:
        if os.path.exists(persistence_file):
            with open(persistence_file, "r") as f:
                state = json.load(f)
            store_name = state.get("store_name")
            
            if store_name:
                from backend.services.rag_service import GeminiRAGService
                from backend.config import settings
                from google import genai
                
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                manual_store = client.file_search_stores.get(name=store_name)
    except Exception as e:
        manual_load_error = str(e)
    
    svc = _get_service()
    
    state_in_file = None
    if os.path.exists(persistence_file):
        with open(persistence_file, "r") as f:
            state_in_file = json.load(f)
    
    return {
        "success": True,
        "message": "Service reloaded",
        "store_loaded": svc.file_search_store is not None,
        "store_name": svc.file_search_store.name if svc.file_search_store else None,
        "manual_load_works": manual_store is not None,
        "manual_load_error": manual_load_error,
        "debug": {
            "service_enabled": svc.enabled,
            "client_exists": svc.client is not None,
            "persistence_file_exists": os.path.exists(persistence_file),
            "store_in_file": state_in_file.get("store_name") if state_in_file else None,
            "files_count": len(svc.uploaded_files),
            "files_in_file": len(state_in_file.get("uploaded_files", [])) if state_in_file else 0
        }
    }

@router.get("/files")
async def files():
    try:
        svc = _get_service()
        return svc.get_files()
    except Exception:
        return {"success": True, "files": [], "store_name": None}

@router.get("/status")
async def status():
    try:
        svc = _get_service()
        return svc.status()
    except Exception:
        return {
            "file_uploaded": False,
            "conversation_length": 0,
            "store_name": None,
            "uploaded_files": [],
            "configured": bool(settings.GEMINI_API_KEY),
        }

@router.get("/api-info")
async def api_info():
    try:
        svc = _get_service()
        return svc.api_info()
    except Exception:
        return {
            "success": False,
            "api_key": settings.GEMINI_API_KEY,
            "store_exists": False,
            "store_name": None,
            "file_count": 0,
            "files": [],
            "model": "gemini-2.5-flash",
            "metadata_keys": [],
        }

@router.post("/update-api-key")
async def update_api_key(payload: dict, user: Optional[dict] = Depends(get_current_user_optional)):
    """Update API key - only admins can do this"""
    if user and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update API key")
    new_key = str(payload.get("api_key", "")).strip()
    svc = _get_service()
    result = svc.update_api_key(new_key)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/extract-questions/{file_index}")
async def extract_questions(file_index: int, user: Optional[dict] = Depends(get_current_user_optional)):
    """Extract questions from an uploaded PDF file using Gemini AI"""
    svc = _get_service()
    result = svc.extract_questions_from_pdf(file_index)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None),
    user: Optional[dict] = Depends(get_current_user_optional)
):
    """Analyze an image and answer questions about it using Gemini Vision"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Save temp file
    os.makedirs(_uploads_dir(), exist_ok=True)
    tmp_path = os.path.join(_uploads_dir(), file.filename)
    
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    svc = _get_service()
    result = svc.analyze_image(tmp_path, question or "")
    
    # Clean up temp file
    try:
        os.remove(tmp_path)
    except Exception:
        pass
    
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result
