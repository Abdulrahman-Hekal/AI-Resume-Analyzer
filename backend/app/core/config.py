import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Resume Analyzer"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & Auth
    SECRET_KEY: str = "super-secret-jwt-signing-key-for-graduation-project-demo-replace-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./data/resume_analyzer.db"

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx"]

    # AI Configuration
    # Options: "cascade", "gemini", "groq", "local"
    AI_PROVIDER: str = "cascade"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # RAG Settings
    RAG_TOP_K: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.15

    # Match Scoring Weights (Formula: Skill*0.4 + Exp*0.25 + Edu*0.15 + Sem*0.2)
    WEIGHT_SKILLS: float = 0.40
    WEIGHT_EXPERIENCE: float = 0.25
    WEIGHT_EDUCATION: float = 0.15
    WEIGHT_SEMANTIC: float = 0.20

    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("WEIGHT_SEMANTIC")
    @classmethod
    def validate_weights(cls, v, info):
        # We can check that weights approximately sum to 1.0
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure critical directories exist
os.makedirs(os.path.dirname(os.path.abspath(settings.DATABASE_URL.replace("sqlite:///", ""))), exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
