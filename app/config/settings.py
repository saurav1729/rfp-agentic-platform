"""
Configuration settings for the FastAPI application
Uses environment variables for sensitive data
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import json


def _env_list(key: str, default: List[str]) -> List[str]:
    """
    Try to read a JSON list from env first, then comma-separated string,
    otherwise return default.
    """
    raw = os.getenv(key)
    if not raw:
        return default
    raw = raw.strip()
    # try JSON list like '["a","b"]'
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(p) for p in parsed]
    except Exception:
        pass
    # fallback: comma separated
    return [p.strip() for p in raw.split(",") if p.strip()]


class Settings(BaseSettings):
    """Application settings"""

    # App Configuration
    APP_NAME: str = "RFP Agentic Platform"
    APP_DESCRIPTION: str = (
        "An autonomous multi-agent AI system for end-to-end RFP processing, "
        "including sales discovery, requirement analysis, pricing intelligence, "
        "proposal drafting and compliance review."
    )
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS Configuration (defaults kept from your file)
    CORS_ORIGINS: List[str] = _env_list(
        "CORS_ORIGINS",
        [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8001",
        ],
    )
    # Optionally override allowed methods/headers via env
    CORS_METHODS: Optional[List[str]] = None
    CORS_HEADERS: Optional[List[str]] = None

    # Trusted hosts for TrustedHostMiddleware (empty list = disabled)
    TRUSTED_HOSTS: List[str] = _env_list("TRUSTED_HOSTS", [])

    # Database Configuration (placeholder; you will add Mongo later)
    DATABASE_URL: str = ""
    DATABASE_ECHO: bool = False

    # MongoDB (optional; set MONGO_URI in .env when you add Mongo)
    MONGO_URI: Optional[str] = os.getenv("MONGO_URI", None)

    # Observability / monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)

    # GenAI API Key
    GENAI_API_KEY: Optional[str] = os.getenv("GENAI_API_KEY", None)

    # LLM Configuration (kept commented / optional)
    # LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    # LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    # LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    # OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Agent Configuration (examples)
    # MAX_AGENT_ITERATIONS: int = 10
    # AGENT_TIMEOUT: int = 300  # 5 minutes

    # RAG Configuration
    # ENABLE_RAG: bool = True
    # VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma")
    # EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
