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

# Determine if using PostgreSQL or SQLite
IS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")
IS_SQLITE = "sqlite" in DATABASE_URL

# Create SQLAlchemy engine with appropriate settings
if IS_POSTGRES:
    # PostgreSQL-specific configuration
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL query logging
        pool_pre_ping=True,  # Verify connections before using
        pool_size=5,  # Connection pool size
        max_overflow=10,  # Max overflow connections
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
elif IS_SQLITE:
    # SQLite-specific configuration
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        echo=False,
        pool_pre_ping=True,
    )
else:
    # Fallback for other databases
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )


# Enable foreign key constraints for SQLite
# SQLite doesn't enforce foreign keys by default
# PostgreSQL enforces them automatically
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite connections."""
    if IS_SQLITE:
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
