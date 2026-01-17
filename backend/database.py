"""
database.py - Database Connection and Session Management

PURPOSE:
    Configure SQLAlchemy database connection to Supabase PostgreSQL.
    Handles connection pooling and session lifecycle.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
from config import settings


def _create_engine():
    """
    Create SQLAlchemy engine with appropriate configuration.

    Detects SQLite vs PostgreSQL and uses appropriate settings:
    - SQLite: Uses StaticPool for in-memory databases, no pool_size/max_overflow
    - PostgreSQL: Uses connection pooling with pool_size and max_overflow
    """
    database_url = settings.DATABASE_URL

    # Check if we are using SQLite (typically for testing)
    if database_url.startswith("sqlite"):
        # SQLite configuration - especially for in-memory databases
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DEBUG,
        )
    else:
        # PostgreSQL configuration with connection pooling
        return create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,  # Connection pool size
            max_overflow=20,  # Max overflow connections
            echo=settings.DEBUG,  # Log SQL queries in debug mode
        )


# Create SQLAlchemy engine
# Using Supabase PostgreSQL connection (or SQLite for tests)
engine = _create_engine()

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.

    Note: In production, use Alembic migrations instead.
    This is only for development/testing.
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized")


# Test database connection on import
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
    raise
