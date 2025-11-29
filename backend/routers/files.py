from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
from urllib.parse import urljoin
import re
import os
import uuid
import time
from typing import Optional
from fastapi import Depends
from backend.middleware.auth import get_current_user_optional

router = APIRouter()

@router.get("/proxy")
async def proxy(url: str = Query(...)):
    if not (url.startswith("https://") or url.startswith("http://")):
        raise HTTPException(status_code=400, detail="invalid_url")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="fetch_failed")
        ct = resp.headers.get("content-type", "application/octet-stream")
        return StreamingResponse(iter([resp.content]), media_type=ct)

@router.get("/resolve-pdf")
async def resolve_pdf(url: str = Query(...)):
    if not (url.startswith("https://") or url.startswith("http://")):
        raise HTTPException(status_code=400, detail="invalid_url")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="fetch_failed")
        ct = resp.headers.get("content-type", "").lower()
        if "application/pdf" in ct or url.lower().endswith(".pdf"):
            return JSONResponse({"pdf_url": resp.url.human_repr()})
        text = resp.text or ""
        m = re.search(r"href=\"([^\"]+\.pdf[^\"]*)\"", text, flags=re.IGNORECASE)
        if not m:
            m = re.search(r"href='([^']+\.pdf[^']*)'", text, flags=re.IGNORECASE)
        if m:
            href = m.group(1)
            pdf_url = urljoin(resp.url.human_repr(), href)
            return JSONResponse({"pdf_url": pdf_url})
        raise HTTPException(status_code=404, detail="pdf_not_found")

def _cache_base_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "data", "tmp")

def _safe_ext(content_type: str, fallback: str = "txt") -> str:
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return "pdf"
    if "html" in ct:
        return "html"
    if "json" in ct:
        return "json"
    if "plain" in ct:
        return "txt"
    return fallback

@router.post("/cache")
async def cache_url(payload: dict, user: Optional[dict] = Depends(get_current_user_optional)):
    url = str(payload.get("url", "")).strip()
    filename = str(payload.get("filename", "")).strip()
    if not url:
        raise HTTPException(status_code=400, detail="invalid_url")
    user_folder = f"user-{user['id']}" if user and user.get("id") else "anon"
    base_dir = _cache_base_dir()
    target_dir = os.path.join(base_dir, user_folder)
    os.makedirs(target_dir, exist_ok=True)
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="fetch_failed")
        ct = resp.headers.get("content-type", "application/octet-stream")
        ext = _safe_ext(ct, "txt")
        if not filename:
            filename = os.path.basename(url) or f"cached-{uuid.uuid4().hex}.{ext}"
        if not re.search(r"\.[a-zA-Z0-9]+$", filename):
            filename = f"{filename}.{ext}"
        target_path = os.path.join(target_dir, filename)
        with open(target_path, "wb") as f:
            f.write(resp.content)
    local_url = f"/cache/{user_folder}/{filename}"
    return {
        "success": True,
        "local_url": local_url,
        "local_path": target_path,
        "content_type": ct,
        "size": len(resp.content),
        "expires_at": int(time.time()) + 60 * 60
    }

@router.get("/cache/list")
async def cache_list(user: Optional[dict] = Depends(get_current_user_optional)):
    user_folder = f"user-{user['id']}" if user and user.get("id") else "anon"
    target_dir = os.path.join(_cache_base_dir(), user_folder)
    if not os.path.exists(target_dir):
        return {"files": []}
    files = []
    for name in os.listdir(target_dir):
        p = os.path.join(target_dir, name)
        if os.path.isfile(p):
            files.append({"name": name, "url": f"/cache/{user_folder}/{name}", "size": os.path.getsize(p)})
    return {"files": files}

@router.delete("/cache/clear")
async def cache_clear(user: Optional[dict] = Depends(get_current_user_optional)):
    user_folder = f"user-{user['id']}" if user and user.get("id") else "anon"
    target_dir = os.path.join(_cache_base_dir(), user_folder)
    if not os.path.exists(target_dir):
        return {"success": True}
    for name in os.listdir(target_dir):
        p = os.path.join(target_dir, name)
        try:
            if os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass
    return {"success": True}
