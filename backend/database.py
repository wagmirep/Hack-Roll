"""
database.py - Database Connection and Session Management

PURPOSE:
    Configure SQLAlchemy database connection and provide session management.
    Handles PostgreSQL connection pooling and session lifecycle.

RESPONSIBILITIES:
    - Create SQLAlchemy engine from DATABASE_URL
    - Configure connection pooling
    - Provide SessionLocal factory for request-scoped sessions
    - Define Base class for all models
    - Provide get_db() dependency for FastAPI

REFERENCED BY:
    - models.py - Imports Base for model definitions
    - main.py - Database initialization on startup
    - routers/sessions.py - Uses get_db() dependency
    - routers/groups.py - Uses get_db() dependency
    - processor.py - Database operations during processing
    - alembic/env.py - Migrations

REFERENCES:
    - config.py - DATABASE_URL setting

EXPORTS:
    - engine: SQLAlchemy engine instance
    - SessionLocal: Session factory
    - Base: Declarative base for models
    - get_db(): FastAPI dependency for database sessions
"""
