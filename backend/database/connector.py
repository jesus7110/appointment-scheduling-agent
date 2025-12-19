"""
Database connector for PostgreSQL using SQLAlchemy.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/appointment_scheduling"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,  # Set to True for SQL query logging
    future=True
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use this in FastAPI route dependencies.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session directly.
    Remember to close it when done.
    
    Returns:
        Database session
    """
    return SessionLocal()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    from .models import Base
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def close_db():
    """Close database connections."""
    engine.dispose()
    logger.info("Database connections closed")

