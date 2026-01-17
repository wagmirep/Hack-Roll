"""
database.py - Database Connection and Session Management

PURPOSE:
    Configure SQLAlchemy database connection to Supabase PostgreSQL.
    Handles connection pooling and session lifecycle.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from config import settings

# Create SQLAlchemy engine
# Using Supabase PostgreSQL connection
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max overflow connections
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

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
    print("✅ Database tables initialized")


# Test database connection on import
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    raise
