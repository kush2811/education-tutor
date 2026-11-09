"""Application core configuration management using Pydantic Settings."""

import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for AI Multimodal Tutor backend."""
    
    PROJECT_NAME: str = "AI-Powered Multimodal Student Tutor"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Server host & port
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    
    # CORS Origins (comma-separated string or list)
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    # Database & Storage
    DATABASE_URL: str = "sqlite:///./tutor.db"
    UPLOAD_DIR: str = "./storage/uploads"
    VECTOR_STORE_DIR: str = "./storage/vector_store"
    
    # Multimodal AI Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # Voice Service Settings
    TTS_PROVIDER: str = "edge-tts"
    STT_PROVIDER: str = "whisper-local"
    
    # Symbolic Math Verification
    ENABLE_SYMPY_VERIFICATION: bool = True

    # Security & Rate Limiting
    ENABLE_RATE_LIMITER: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
