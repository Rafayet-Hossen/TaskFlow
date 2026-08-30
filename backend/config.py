import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "TaskFlow"
    VERSION: str = "1.0.0"
    
    # Database Settings
    # Default to PostgreSQL, with flexible URL configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/taskflow_db"
    )
    
    # Fallback SQLite DB path if PostgreSQL is unavailable in local dev
    SQLITE_FALLBACK_URL: str = f"sqlite:///{BASE_DIR}/taskflow_dev.db"
    
    # JWT Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "taskflow-super-secure-jwt-secret-key-at-least-64-characters-long-2026-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
    
    # Verification Code Settings
    VERIFICATION_CODE_EXPIRE_MINUTES: int = int(os.getenv("VERIFICATION_CODE_EXPIRE_MINUTES", "15"))
    
    # Email / SMTP Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "no-reply@taskflow.app")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "TaskFlow")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes")
    
    # Dev Mode: If True, prints verification & reset codes to console and API responses for instant testing
    DEV_MODE: bool = os.getenv("DEV_MODE", "True").lower() in ("true", "1", "yes")

settings = Settings()
