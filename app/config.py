from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/transactions_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Application
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: int = 2  # seconds
    
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
    
    # Domestic merchants
    DOMESTIC_MERCHANTS: list = [
        "Swiggy",
        "Ola",
        "IRCTC",
        "Zomato",
        "Flipkart",
        "Paytm",
        "PhonePe",
        "Jio"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
