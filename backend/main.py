from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os, sys

# Add project root to path (for both local and Docker)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# IMPORTANT: Import patch_passlib BEFORE any other imports that use passlib
# This prevents wrap bug detection errors during bcrypt initialization
try:
    from backend.utils.patch_passlib import *
except Exception as e:
    import logging
    logging.warning(f"Could not apply passlib patch: {e}")

from backend.config import settings
settings.ENABLE_CLOUDFLARE = bool(os.getenv("ENABLE_CLOUDFLARE")) or ("--cloudflare" in sys.argv)
from backend.utils import r2
from backend.routers import auth, posts, exams, users, rag, files, cyber
from backend.routers import admin_teachers, teacher_classrooms, teacher_notifications, teacher_posts, teacher_exams, subjects
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan event handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME}")
    logger.info(f"📊 Database: {'Cloudflare D1' if settings.use_cloudflare_d1 else 'SQLite'}")
    storage_msg = (
        f"Cloudflare R2 ({settings.CLOUDFLARE_R2_BUCKET_NAME})" if getattr(r2, "available", False) else "R2 disabled"
    )
    logger.info(f"💾 Storage: {storage_msg}")
    yield
    # Shutdown
    logger.info(f"👋 Shutting down {settings.APP_NAME}")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    🎓 Education API with Cloudflare D1 and R2 Storage
    
    ## Features
    * 🔐 JWT Authentication
    * 📚 Posts Management
    * 📝 Exams Management
    * ☁️ Cloud Storage (R2)
    * 🗄️ Database (D1 or SQLite)
    """,
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    
    # Convert validation errors to Vietnamese messages
    error_messages = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        error_type = error.get("type", "")
        msg = error.get("msg", "")
        
        # Map common validation errors to Vietnamese
        if error_type == "value_error.email":
            error_messages.append(f"Email không hợp lệ: {field}")
        elif error_type == "value_error.missing":
            error_messages.append(f"Thiếu trường bắt buộc: {field}")
        elif "min_length" in msg:
            error_messages.append(f"{field}: Giá trị quá ngắn")
        elif "max_length" in msg:
            error_messages.append(f"{field}: Giá trị quá dài")
        elif "pattern" in msg:
            error_messages.append(f"{field}: Định dạng không đúng")
        else:
            error_messages.append(f"{field}: {msg}")
    
    detail_message = "; ".join(error_messages) if error_messages else "Dữ liệu không hợp lệ"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": detail_message,
            "errors": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    
    # Map common errors to Vietnamese messages
    error_message = "Đã xảy ra lỗi. Vui lòng thử lại sau."
    
    if isinstance(exc, HTTPException):
        # If it's already an HTTPException, use its detail
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            },
        )
    
    # Handle specific error types - extract clean error message
    error_str = str(exc).lower()
    error_type = type(exc).__name__
    
    # Check for password length errors
    if "password" in error_str and ("72" in error_str or "longer" in error_str):
        error_message = "Mật khẩu quá dài. Vui lòng sử dụng mật khẩu ngắn hơn 72 ký tự."
    # Check for ValueError with password
    elif isinstance(exc, ValueError) and "password" in error_str:
        error_message = "Mật khẩu không hợp lệ. Vui lòng kiểm tra lại."
    # Check for validation errors
    elif "validation" in error_str or "pydantic" in error_str or error_type == "ValidationError":
        error_message = "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại thông tin nhập vào."
    # Check for database errors
    elif "database" in error_str or "sql" in error_str or "operationalerror" in error_str:
        error_message = "Lỗi kết nối cơ sở dữ liệu. Vui lòng thử lại sau."
    # Never show full traceback to user, even in debug mode
    # Only show the exception type and a clean message
    elif settings.DEBUG:
        # In debug mode, show exception type but not full traceback
        error_message = f"Lỗi {error_type}: {error_message}"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": error_message,
            "timestamp": datetime.utcnow().isoformat()
        },
    )

# Include Routers
app.include_router(
    auth.router,
    prefix="/api",
    tags=["🔐 Authentication"]
)

app.include_router(
    posts.router,
    prefix="/api/posts",
    tags=["📚 Posts"]
)

app.include_router(
    exams.router,
    prefix="/api/exams",
    tags=["📝 Exams"]
)

app.include_router(
    users.router,
    prefix="/api/users",
    tags=["👤 Users"]
)

app.include_router(
    rag.router,
    prefix="/api/rag",
    tags=["🤖 RAG"]
)

app.include_router(
    files.router,
    prefix="/api/files",
    tags=["📄 Files"]
)

app.include_router(
    cyber.router,
    prefix="/api/cyber",
    tags=["🛡️ Cyber Security"]
)

# Serve cached files statically for PDF viewing
try:
    # Use same path calculation as files.py router
    CACHE_DIR = os.path.join(project_root, "frontend", "data", "tmp")
    os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure directory exists
    app.mount("/cache", StaticFiles(directory=CACHE_DIR), name="cache")
    logger.info(f"Serving cache files from: {CACHE_DIR}")
except Exception as e:
    logger.warning(f"Could not mount cache directory: {e}")
    pass

# Admin Routes
app.include_router(
    admin_teachers.router,
    tags=["👨‍🏫 Admin - Teachers"]
)

# Teacher Routes
app.include_router(
    teacher_classrooms.router,
    tags=["🏫 Teacher - Classrooms"]
)

app.include_router(
    teacher_notifications.router,
    tags=["🔔 Teacher - Notifications"]
)

app.include_router(
    teacher_posts.router,
    tags=["📚 Teacher - Posts"]
)

app.include_router(
    teacher_exams.router,
    tags=["📝 Teacher - Exams"]
)

app.include_router(
    subjects.router,
    tags=["📘 Subjects"]
)

# Root Endpoints
@app.get("/", tags=["Health"])
async def root():
    """API Root - Health Check"""
    return {
        "name": settings.APP_NAME,
        "status": "healthy",
        "version": "1.0.0",
        "database": "D1" if settings.use_cloudflare_d1 else "SQLite",
        "storage": "R2",
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "type": "D1" if settings.use_cloudflare_d1 else "SQLite",
            "connected": True
        },
        "storage": {
            "type": "R2",
            "bucket": settings.CLOUDFLARE_R2_BUCKET_NAME
        }
    }

# Run application
if __name__ == "__main__":
    import uvicorn
    # Determine the correct app path based on where we're running from
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # If running from backend directory, use backend.main:app
    # If running from project root, also use backend.main:app
    app_path = "backend.main:app"
    
    uvicorn.run(
        app_path,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
