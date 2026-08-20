from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import logging
import logging.handlers
import traceback
from datetime import datetime as _dt
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.utils.seed_knowledge import seed_knowledge_points
from app.utils.seed_scoring import seed_scoring_schemes
from app.api.v1 import auth, schools, students, subjects, exams, scores, analysis, report, exam_detail


# Setup structured logging
import sys as _sys
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

# File handler (all levels)
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"), maxBytes=10*1024*1024, backupCount=5
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATEFMT))

# Error file handler
error_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "error.log"), maxBytes=10*1024*1024, backupCount=3
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATEFMT))

# Console handler
console_handler = logging.StreamHandler(_sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATEFMT))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, error_handler, console_handler])
logger = logging.getLogger("exam_analysis")


class ErrorLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            if response.status_code >= 500:
                logger.error("%s %s -> %d", request.method, request.url.path, response.status_code)
            return response
        except Exception as e:
            tb = traceback.format_exc()
            logger.error("Unhandled error: %s %s\n%s", request.method, request.url.path, tb)
            raise


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    print("Database tables created")
    seed_knowledge_points()
    print("Knowledge points seeded")
    seed_scoring_schemes()
    print("Scoring schemes seeded")
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ErrorLogMiddleware)


@app.get("/health/llm")
def health_llm():
    """LLM 连通性测试"""
    if not settings.LLM_ENABLED or not settings.LLM_API_KEY:
        return {"status": "disabled", "detail": "未配置 LLM_API_KEY 或 LLM_ENABLED=false"}
    try:
        import httpx
        base = settings.LLM_API_BASE.rstrip("/")
        resp = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"}, timeout=5)
        return {"status": "ok" if resp.status_code == 200 else "error", "status_code": resp.status_code}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/health")
def health():
    """健康检查接口"""
    import platform
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": _dt.now().isoformat(),
        "python": platform.python_version(),
        "debug": settings.DEBUG,
        "llm_enabled": settings.LLM_ENABLED,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    tb = traceback.format_exc()
    logger.error("Unhandled %s: %s %s\n%s", type(exc).__name__, request.method, request.url.path, tb)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请查看日志"},
    )

app.include_router(auth.router, prefix="/api/v1")
app.include_router(schools.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(exams.router, prefix="/api/v1")
app.include_router(scores.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(exam_detail.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API", "version": settings.APP_VERSION}
