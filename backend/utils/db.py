from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.models import Base
import os

from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present (local development)
backend_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=backend_env)
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=root_env)
load_dotenv()

# Auto-detect database from environment
# Render provides DATABASE_URL automatically for PostgreSQL
# Locally falls back to SQLite (zero setup needed)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./darkpattern.db")

# Render PostgreSQL URLs start with postgres:// — SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Reconnect if connection dropped (important for cloud DBs)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables on startup"""
    Base.metadata.create_all(bind=engine)
    db_type = "SQLite (local)" if DATABASE_URL.startswith("sqlite") else "PostgreSQL"
    print(f"[DATABASE] Initialized using {db_type}")


def get_db():
    """Dependency injection for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
