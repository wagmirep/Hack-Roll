"""
alembic/env.py - Alembic Environment Configuration

PURPOSE:
    Configure Alembic migration environment.
    Connects to database and sets up migration context.

RESPONSIBILITIES:
    - Load database URL from config
    - Import all models for autogenerate
    - Configure online and offline migration modes
    - Set up logging

REFERENCED BY:
    - alembic command line tool
    - alembic.ini

REFERENCES:
    - ../config.py - DATABASE_URL
    - ../models.py - SQLAlchemy models for autogenerate
    - ../database.py - Base metadata

CONFIGURATION:
    - Loads DATABASE_URL from environment
    - Uses SQLAlchemy Base.metadata for autogenerate
    - Supports both sync and async migrations
"""
