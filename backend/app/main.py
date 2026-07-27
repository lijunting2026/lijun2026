from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
import logging
import traceback
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import auth, schools, students, subjects, exams, scores, analysis, report


# Setup error logging
LOG_FILE = "logs/error.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
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
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ErrorLogMiddleware)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(schools.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(exams.router, prefix="/api/v1")
app.include_router(scores.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API", "version": settings.APP_VERSION}


@app.get("/health")
def health():
    return {"status": "ok"}
