"""Application configuration using Pydantic Settings"""
import json
from functools import lru_cache
from typing import Any, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "SmartDiner"
    app_env: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://restaurant_user:restaurant_pass@127.0.0.1:5433/restaurant_db",
        description="PostgreSQL async connection string"
    )
    
    # LLM API Keys
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    azure_openai_endpoint: str = Field(default="", description="Azure OpenAI endpoint")
    azure_openai_api_key: str = Field(default="", description="Azure OpenAI API key")
    azure_openai_deployment: str = Field(default="gpt-4o", description="Azure OpenAI deployment name")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", description="JWT secret key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    cors_origin_regex: str = Field(
        default=r"^https://.*\.vercel\.app$",
        description="Optional regex for allowed origins (useful for preview deployments)"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> List[str]:
        """Allow JSON array or comma-separated origins from environment variables."""
        if value is None:
            return []

        if isinstance(value, list):
            return [origin.rstrip("/") for origin in value if isinstance(origin, str)]

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [
                            origin.rstrip("/")
                            for origin in parsed
                            if isinstance(origin, str)
                        ]
                except json.JSONDecodeError:
                    pass

            return [
                origin.strip().rstrip("/")
                for origin in raw.split(",")
                if origin.strip()
            ]

        return []


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()