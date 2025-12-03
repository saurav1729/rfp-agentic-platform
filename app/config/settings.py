"""
Configuration settings for the FastAPI application
Uses environment variables for sensitive data
"""

from pydantic_settings import BaseSettings
from typing import List
import os


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
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8001",
    ]
    
    # Database Configuration
    DATABASE_URL: str = ""        
    DATABASE_ECHO: bool = False     
    
    # LLM Configuration
    # LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    # LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4")
    # LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    # OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Agent Configuration
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
