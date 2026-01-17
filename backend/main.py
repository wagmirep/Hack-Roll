"""
main.py - FastAPI Application Entry Point

PURPOSE:
    Main FastAPI application that defines the API server and includes all routers.
    This is the entry point for running the backend with `uvicorn main:app --reload`.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database import engine, Base
from schemas import HealthResponse, ErrorResponse

# Import routers
from routers import auth, groups, sessions, stats

# Create FastAPI app
app = FastAPI(
    title="LahStats API",
    description="Singlish word tracking API for friend groups",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    print(f"❌ Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.DEBUG else "An unexpected error occurred",
            status_code=500
        ).dict()
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("=" * 60)
    print("🚀 LahStats API Starting Up")
    print("=" * 60)
    print(f"📍 Environment: {'Development' if settings.DEBUG else 'Production'}")
    print(f"🌐 Supabase URL: {settings.SUPABASE_URL}")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print(f"📡 CORS origins: {settings.CORS_ORIGINS}")
    print("=" * 60)
    
    # Create tables if they don't exist (for development only)
    # In production, use Alembic migrations
    if settings.DEBUG:
        print("🔨 Creating database tables (development mode)...")
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables ready")
        except Exception as e:
            print(f"⚠️  Database table creation skipped: {e}")
    
    print("✅ Application startup complete")
    print("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("👋 LahStats API shutting down...")


# Health check endpoint
@app.get("/", response_model=HealthResponse, tags=["Health"])
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        Health status information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database="connected",
        version="1.0.0"
    )


# Include routers
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(sessions.router)
app.include_router(stats.router)


# Root redirect to docs
@app.get("/docs-redirect", include_in_schema=False)
async def docs_redirect():
    """Redirect to API documentation"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting LahStats API server...")
    print(f"📍 Running on http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API docs available at http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
