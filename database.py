from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create engine with optimized pool settings for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_size=20,  # Increase base pool size
    max_overflow=30,  # Increase max overflow connections
    pool_timeout=60,  # Increase timeout to 60 seconds
    pool_pre_ping=True  # Enable connection health checks
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def drop_and_recreate_tables():
    """Drop all tables and recreate them"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def init_db():
    """Initialize database and create all tables"""
    # Import here to avoid circular imports
    import models  # noqa
    drop_and_recreate_tables()
    return True 