import httpx
from typing import Optional, Dict
from backend.config import settings

DEFAULT_TIMEOUT = 20.0

def build_headers(token: Optional[str] = None, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    return headers

def get_async_client(base_url: Optional[str] = None, token: Optional[str] = None) -> httpx.AsyncClient:
    if base_url is None:
        base_url = settings.EXTERNAL_API_BASE_URL or ""
    headers = build_headers(token or settings.EXTERNAL_API_TOKEN)
    return httpx.AsyncClient(base_url=base_url, headers=headers, timeout=DEFAULT_TIMEOUT)
