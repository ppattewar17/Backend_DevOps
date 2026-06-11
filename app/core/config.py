from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration"""
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI-Powered Transaction Processing Pipeline"
    VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@db:5432/transactions_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # OpenAI API
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Application
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_MULTIPLIER: int = 1  # 1s, 2s, 4s
    
    # Categories
    VALID_CATEGORIES: list = [
        "Food",
        "Shopping",
        "Travel",
        "Transport",
        "Utilities",
        "Cash Withdrawal",
        "Entertainment",
        "Other"
    ]
    
    # Domestic merchants (for anomaly detection)
    DOMESTIC_MERCHANTS: list = [
        "Swiggy",
        "Ola",
        "IRCTC"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
