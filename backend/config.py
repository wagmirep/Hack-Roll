"""
config.py - Application Configuration

PURPOSE:
    Centralized configuration management using environment variables.
    Provides typed settings with defaults and validation.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Database Configuration (Supabase PostgreSQL)
    DATABASE_URL: Optional[str] = None
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Configuration
    CORS_ORIGINS: list[str] = [
        "http://localhost:8081",  # Expo dev server
        "http://localhost:19006",  # Expo web
        "exp://localhost:8081",   # Expo app
        "*"  # Allow all for development
    ]
    
    # Storage Configuration (Supabase Storage)
    STORAGE_BUCKET: str = "audio-chunks"
    
    # ML Models Configuration
    HUGGINGFACE_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")
    
    # Redis Configuration (optional, for background jobs)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Firebase Configuration (optional, for real-time updates)
    FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_CREDENTIALS: Optional[str] = os.getenv("FIREBASE_CREDENTIALS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construct DATABASE_URL from SUPABASE_URL if not provided
        if not self.DATABASE_URL and self.SUPABASE_URL:
            # Extract project reference from Supabase URL
            # Format: https://PROJECT_REF.supabase.co
            project_ref = self.SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
            # Construct PostgreSQL connection string
            # Format: postgresql://postgres:[PASSWORD]@db.PROJECT_REF.supabase.co:5432/postgres
            # Note: Password needs to be set separately or use service role key
            self.DATABASE_URL = f"postgresql://postgres.{project_ref}:postgres@aws-0-us-east-1.pooler.supabase.com:6543/postgres"


# Create global settings instance
settings = Settings()

# Validate required settings
if not settings.SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not settings.SUPABASE_JWT_SECRET:
    raise ValueError("SUPABASE_JWT_SECRET environment variable is required")

print(f"✅ Configuration loaded successfully")
print(f"   Supabase URL: {settings.SUPABASE_URL}")
print(f"   Database URL: {settings.DATABASE_URL[:50]}...")
print(f"   Debug mode: {settings.DEBUG}")
