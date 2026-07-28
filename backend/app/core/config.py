from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    APP_NAME: str = "考试质量分析系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # SQLite for local dev, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./exam_analysis.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Security
    BCRYPT_ROUNDS: int = 12
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:80", "http://127.0.0.1:5173"]

    # LLM settings for AI chat
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_ENABLED: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
