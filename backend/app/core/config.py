import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "RAS-RAG"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Security & JWT
    SECRET_KEY: str = "ras_rag_secure_production_key_b947c8d9e2a14f6890f5c1d87e2b"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = "sqlite:///./data/ras_rag.db"

    # Storage paths
    UPLOAD_DIR: str = "./data/uploads"
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    MAX_FILE_SIZE_MB: int = 15

    # Local AI & RAG Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    FALLBACK_LLM_ENABLED: bool = True

    # Risk Engine Thresholds & Weights
    RISK_WEIGHT_QUERY: float = 0.45
    RISK_WEIGHT_SESSION: float = 0.35
    RISK_WEIGHT_DOC_SENSITIVITY: float = 0.20

    THRESHOLD_ALLOW: float = 30.0
    THRESHOLD_RESTRICT: float = 60.0
    THRESHOLD_VERIFY: float = 80.0

    # Default Seed Credentials
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@rasrag.local"
    DEFAULT_ADMIN_PASSWORD: str = "AdminSecure@2026"
    DEFAULT_USER_USERNAME: str = "analyst"
    DEFAULT_USER_EMAIL: str = "analyst@rasrag.local"
    DEFAULT_USER_PASSWORD: str = "UserSecure@2026"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


# Instantiate singleton settings
settings = Settings()

# Ensure required runtime directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs("./data", exist_ok=True)
