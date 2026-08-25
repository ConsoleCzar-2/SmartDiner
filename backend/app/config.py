"""Application configuration using Pydantic Settings"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


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
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()