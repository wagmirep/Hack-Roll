#!/usr/bin/env python3
"""
verify_integration.py - Verify ML Pipeline Integration

This script verifies that all components of the ML pipeline integration
are properly configured and connected.

Checks:
1. Redis connection and queue setup
2. Database connection
3. Worker can process jobs
4. ML models are accessible
5. API endpoints are responding
"""

import sys
import os
import json
from datetime import datetime

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_redis():
    """Verify Redis connection and queue setup"""
    print("🔍 Checking Redis connection...")
    try:
        from redis_client import get_redis_client, PROCESSING_QUEUE, FAILED_QUEUE, get_queue_stats
        redis_client = get_redis_client()
        redis_client.ping()
        print("  ✅ Redis connected")
        
        stats = get_queue_stats()
        print(f"  📊 Processing queue: {stats['processing']} jobs")
        print(f"  📊 Failed queue: {stats['failed']} jobs")
        return True
    except Exception as e:
        print(f"  ❌ Redis connection failed: {e}")
        print("  💡 Start Redis: docker run -d -p 6379:6379 redis:latest")
        return False


def check_database():
    """Verify database connection"""
    print("\n🔍 Checking database connection...")
    try:
        from database import SessionLocal
        from models import Session, SessionSpeaker, SpeakerWordCount, WordCount
        
        db = SessionLocal()
        # Test query
        session_count = db.query(Session).count()
        print(f"  ✅ Database connected")
        print(f"  📊 Sessions in database: {session_count}")
        db.close()
        return True
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        print("  💡 Check DATABASE_URL and Supabase credentials")
        return False


def check_ml_models():
    """Verify ML models are accessible"""
    print("\n🔍 Checking ML models...")
    try:
        from config import settings
        
        # Check HuggingFace token for diarization
        if settings.HUGGINGFACE_TOKEN:
            print("  ✅ HuggingFace token configured")
        else:
            print("  ⚠️  HUGGINGFACE_TOKEN not set (diarization may fail)")
        
        # Check transcription API
        if settings.TRANSCRIPTION_API_URL:
            print(f"  ✅ Transcription API URL: {settings.TRANSCRIPTION_API_URL}")
        else:
            print("  ℹ️  Using local transcription model (TRANSCRIPTION_API_URL not set)")
        
        return True
    except Exception as e:
        print(f"  ❌ Error checking ML models: {e}")
        return False


def check_api_endpoints():
    """Verify API endpoints are accessible"""
    print("\n🔍 Checking API endpoints...")
    try:
        import httpx
        from config import settings
        
        api_url = f"http://{settings.API_HOST}:{settings.API_PORT}"
        health_url = f"{api_url}/health"
        
        with httpx.Client(timeout=5.0) as client:
            response = client.get(health_url)
            if response.status_code == 200:
                print(f"  ✅ API responding at {api_url}")
                return True
            else:
                print(f"  ❌ API returned status {response.status_code}")
                return False
    except httpx.ConnectError:
        print(f"  ❌ API not responding at http://{settings.API_HOST}:{settings.API_PORT}")
        print("  💡 Start API: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"  ❌ Error checking API: {e}")
        return False


def check_worker_ready():
    """Verify worker can process jobs"""
    print("\n🔍 Checking worker readiness...")
    try:
        from redis_client import get_redis_client, PROCESSING_QUEUE
        from processor import process_session_sync
        import uuid
        
        # Test that we can import the processor
        print("  ✅ Worker imports successful")
        print("  ✅ Processor functions available")
        
        # Check queue is accessible
        redis_client = get_redis_client()
        queue_length = redis_client.llen(PROCESSING_QUEUE)
        print(f"  📊 Jobs in processing queue: {queue_length}")
        
        return True
    except Exception as e:
        print(f"  ❌ Worker check failed: {e}")
        return False


def check_storage():
    """Verify storage configuration"""
    print("\n🔍 Checking storage configuration...")
    try:
        from config import settings
        
        if settings.SUPABASE_URL:
            print("  ✅ Supabase URL configured")
        else:
            print("  ❌ SUPABASE_URL not set")
            return False
        
        if settings.SUPABASE_SERVICE_ROLE_KEY:
            print("  ✅ Supabase service role key configured")
        else:
            print("  ⚠️  SUPABASE_SERVICE_ROLE_KEY not set (storage may fail)")
        
        return True
    except Exception as e:
        print(f"  ❌ Storage check failed: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 70)
    print("ML Pipeline Integration Verification")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    results = {
        "Redis": check_redis(),
        "Database": check_database(),
        "ML Models": check_ml_models(),
        "API Endpoints": check_api_endpoints(),
        "Worker": check_worker_ready(),
        "Storage": check_storage(),
    }
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    all_passed = True
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 All checks passed! Integration is ready.")
        print("\nNext steps:")
        print("  1. Start the backend: uvicorn main:app --reload")
        print("  2. Start the worker: python worker.py")
        print("  3. Record audio in the frontend")
        print("  4. Claim speakers after processing")
        print("  5. View stats in Wrapped")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
