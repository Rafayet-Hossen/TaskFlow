import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

logger = logging.getLogger(__name__)

# Try connecting to PostgreSQL first, fallback to SQLite if unavailable in dev
def create_db_engine():
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("postgresql"):
            # Test PostgreSQL connection with a short timeout
            engine = create_engine(
                db_url,
                connect_args={"connect_timeout": 3},
                pool_pre_ping=True
            )
            # Try connecting
            with engine.connect():
                logger.info(f"Connected successfully to PostgreSQL at {db_url}")
                return engine, db_url
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite for local development: {settings.SQLITE_FALLBACK_URL}")
        
    # SQLite fallback
    fallback_engine = create_engine(
        settings.SQLITE_FALLBACK_URL,
        connect_args={"check_same_thread": False}
    )
    return fallback_engine, settings.SQLITE_FALLBACK_URL

engine, ACTIVE_DATABASE_URL = create_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session management"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

