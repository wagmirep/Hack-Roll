"""
config.py - Application Configuration

PURPOSE:
    Centralized configuration management using environment variables.
    Provides typed settings with defaults and validation.

RESPONSIBILITIES:
    - Load environment variables from .env file
    - Provide typed configuration objects
    - Validate required settings on startup
    - Expose settings to other modules

REFERENCED BY:
    - main.py - App configuration
    - database.py - DATABASE_URL
    - storage.py - S3 credentials
    - worker.py - Redis URL
    - services/diarization.py - HuggingFace token
    - services/firebase.py - Firebase credentials

REFERENCES:
    - .env file (via python-dotenv)

SETTINGS:
    Database:
        - DATABASE_URL: PostgreSQL connection string

    Redis:
        - REDIS_URL: Redis connection string

    Storage:
        - S3_BUCKET: S3 bucket name
        - AWS_ACCESS_KEY_ID: AWS access key
        - AWS_SECRET_ACCESS_KEY: AWS secret key
        - AWS_REGION: AWS region (default: us-east-1)

    Models:
        - HUGGINGFACE_TOKEN: For pyannote authentication

    Firebase:
        - FIREBASE_PROJECT_ID: Firebase project ID
        - FIREBASE_CREDENTIALS: Path to service account JSON

    App:
        - DEBUG: Enable debug mode (default: False)
        - API_HOST: API host (default: 0.0.0.0)
        - API_PORT: API port (default: 8000)
"""
