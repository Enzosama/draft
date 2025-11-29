import httpx
import logging
import time
import sqlite3
import aiosqlite
from typing import List, Dict, Any, Optional
from backend.config import settings
from contextlib import asynccontextmanager

class Database:
    def __init__(self):
        self.use_d1 = settings.use_cloudflare_d1
        self.logger = logging.getLogger("db")
        db_url = settings.DATABASE_URL.replace("sqlite:///", "")
        # Handle relative paths - resolve to absolute path
        import os
        if not os.path.isabs(db_url):
            # Get project root
            # __file__ is backend/database/d1.py
            # os.path.dirname(__file__) = backend/database
            # os.path.dirname(os.path.dirname(__file__)) = backend
            # os.path.dirname(os.path.dirname(os.path.dirname(__file__))) = project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Prefer backend/cyber_chat.sqlite if it exists
            backend_db = os.path.join(project_root, "backend", "cyber_chat.sqlite")
            root_db = os.path.join(project_root, "cyber_chat.sqlite")
            
            # Prefer backend/cyber_chat.sqlite if it exists, otherwise use what's specified
            if os.path.exists(backend_db):
                self.db_path = backend_db
            elif os.path.exists(root_db):
                self.db_path = root_db
            elif db_url == "./db.sqlite" or db_url == "db.sqlite":
                # Default to backend/cyber_chat.sqlite
                self.db_path = backend_db
            else:
                # Use absolute path from current working directory
                self.db_path = os.path.abspath(db_url)
        else:
            self.db_path = db_url
        
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                self.logger.warning(f"Could not create database directory {db_dir}: {e}")
        
        if self.use_d1:
            self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
            self.database_id = settings.CLOUDFLARE_DATABASE_ID
            self.api_token = settings.CLOUDFLARE_API_TOKEN
            self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/d1/database/{self.database_id}"
            self.logger.info("db_backend=d1")
        else:
            self._init_sqlite()
            self.logger.info("db_backend=sqlite")
        # Always ensure SQLite exists for runtime fallback when D1 errors
        try:
            import os
            if not os.path.exists(self.db_path):
                self._init_sqlite()
        except Exception:
            pass
    
    def _init_sqlite(self):
        """Initialize SQLite database with schema"""
        import os
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Could not create database directory {db_dir}: {e}")
                raise
        
        db_exists = os.path.exists(self.db_path)
        try:
            conn = sqlite3.connect(self.db_path)
        except Exception as e:
            self.logger.error(f"Could not connect to database at {self.db_path}: {e}")
            raise
        if not db_exists:
            base_dir = os.path.dirname(__file__)
            schema_path = os.path.join(base_dir, "cyber_schema.sql")
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()
        # Ensure users table has phone column for backward compatibility
        try:
            cur = conn.execute("PRAGMA table_info(users)")
            cols = [row[1] for row in cur.fetchall()]
            if "phone" not in cols:
                conn.execute("ALTER TABLE users ADD COLUMN phone TEXT")
                conn.commit()
        except Exception:
            pass
        conn.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Cloudflare API"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    # ==================== CLOUDFLARE D1 METHODS ====================
    
    async def _execute_d1(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query on Cloudflare D1"""
        t0 = time.perf_counter()
        verb = sql.strip().split()[0].upper()
        try:
            async with httpx.AsyncClient() as client:
                payload = {"sql": sql}
                if params:
                    payload["params"] = params
                response = await client.post(
                    f"{self.base_url}/query",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                latency_ms = int((time.perf_counter() - t0) * 1000)
                self.logger.info(f"d1 {verb} status={response.status_code} latency_ms={latency_ms}")
                return data
        except Exception:
            # Fallback to SQLite on any D1 error
            self.logger.error("d1_error_fallback_sqlite")
            return await self._execute_sqlite(sql, params)
    
    # ==================== SQLITE METHODS ====================
    
    async def _execute_sqlite(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query on SQLite"""
        t0 = time.perf_counter()
        verb = sql.strip().split()[0].upper()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if params is None:
                params = []
            
            cursor = await db.execute(sql, params)
            
            # Check if it's a SELECT query
            if sql.strip().upper().startswith("SELECT"):
                rows = await cursor.fetchall()
                results = [dict(row) for row in rows]
                data = {
                    "success": True,
                    "result": [{
                        "results": results,
                        "meta": {"rows_read": len(results)}
                    }]
                }
                latency_ms = int((time.perf_counter() - t0) * 1000)
                self.logger.info(f"sqlite {verb} rows_read={len(results)} latency_ms={latency_ms}")
                return data
            else:
                await db.commit()
                data = {
                    "success": True,
                    "result": [{
                        "results": [],
                        "meta": {
                            "changes": cursor.rowcount,
                            "last_row_id": cursor.lastrowid
                        }
                    }]
                }
                latency_ms = int((time.perf_counter() - t0) * 1000)
                self.logger.info(f"sqlite {verb} changes={cursor.rowcount} latency_ms={latency_ms}")
                return data
    
    # ==================== UNIFIED INTERFACE ====================
    
    async def execute(self, sql: str, params: Optional[List] = None) -> Dict[str, Any]:
        """Execute SQL query (auto-selects D1 or SQLite)"""
        if self.use_d1:
            return await self._execute_d1(sql, params)
        else:
            return await self._execute_sqlite(sql, params)
    
    async def fetch_one(self, sql: str, params: Optional[List] = None) -> Optional[Dict]:
        """Fetch single row"""
        result = await self.execute(sql, params)
        if result.get("success") and result.get("result"):
            results = result["result"][0].get("results", [])
            return results[0] if results else None
        return None
    
    async def fetch_all(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """Fetch all rows"""
        result = await self.execute(sql, params)
        if result.get("success") and result.get("result"):
            return result["result"][0].get("results", [])
        return []
    
    async def insert(self, sql: str, params: Optional[List] = None) -> Optional[int]:
        """Insert and return last insert id"""
        result = await self.execute(sql, params)
        if result.get("success") and result.get("result"):
            meta = result["result"][0].get("meta", {})
            return meta.get("last_row_id")
        return None
    
    async def update(self, sql: str, params: Optional[List] = None) -> int:
        """Update and return affected rows"""
        result = await self.execute(sql, params)
        if result.get("success") and result.get("result"):
            meta = result["result"][0].get("meta", {})
            return meta.get("changes", 0)
        return 0
    
    async def delete(self, sql: str, params: Optional[List] = None) -> int:
        """Delete and return affected rows"""
        return await self.update(sql, params)

# Singleton instance
db = Database()
