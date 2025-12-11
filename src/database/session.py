"""
Database session management for Personal AI Assistant.

Provides SQLAlchemy engine, session factory, and connection management
for SQLite database with proper cleanup and dependency injection.
"""

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from ..models.base import Base


# Get database URL from environment or use default SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# Create SQLAlchemy engine
# For SQLite: 
# - check_same_thread=False allows multiple threads (FastAPI is async)
# - connect_args only used for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL query logging in development
    pool_pre_ping=True,  # Verify connections before using them
)


# Enable foreign key constraints for SQLite
# SQLite doesn't enforce foreign keys by default
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite connections."""
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Create session factory
# autocommit=False: Changes must be explicitly committed
# autoflush=False: Manual control over when to flush to DB
# bind=engine: Tie sessions to our engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """
    Initialize database by creating all tables.
    
    This creates all tables defined in Base.metadata (all our SQLAlchemy models).
    Should be called once at application startup.
    
    Note: In production, use Alembic migrations instead of this.
    """
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    Creates a new SQLAlchemy session for each request,
    yields it to the route handler, then ensures cleanup.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: Database session
        
    Note: Session is automatically closed after request completes,
          even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
