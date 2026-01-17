"""
main.py - FastAPI Application Entry Point

PURPOSE:
    Main FastAPI application that defines the API server and includes all routers.
    This is the entry point for running the backend with `uvicorn main:app --reload`.

RESPONSIBILITIES:
    - Initialize FastAPI app with CORS middleware
    - Include routers from routers/ directory
    - Define health check endpoint
    - Configure app metadata (title, description, version)

REFERENCED BY:
    - uvicorn command (entry point)
    - docker-compose.yml (container startup)
    - deploy.sh (deployment script)

REFERENCES:
    - routers/sessions.py - Session management endpoints
    - routers/groups.py - Group statistics endpoints
    - config.py - Application configuration
    - database.py - Database connection setup

ENDPOINTS EXPOSED:
    GET  /health                    - Health check
    POST /sessions/start            - Create recording session
    POST /sessions/{id}/upload      - Upload audio chunks
    POST /sessions/{id}/end         - Stop & trigger processing
    GET  /sessions/{id}/status      - Poll processing progress
    GET  /sessions/{id}/speakers    - Get claiming data
    POST /sessions/{id}/claim       - User claims speaker
    GET  /groups/{id}/stats         - Group statistics
"""
