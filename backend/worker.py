"""
worker.py - Background Job Worker

PURPOSE:
    Redis-based background job processor. Listens for processing tasks
    from the queue and executes them asynchronously.

RESPONSIBILITIES:
    - Connect to Redis queue
    - Listen for new processing jobs
    - Execute processor.process_session() for each job
    - Handle job failures and retries
    - Update job status in Redis

REFERENCED BY:
    - docker-compose.yml - Runs as separate container/process
    - deploy.sh - Started alongside main API

REFERENCES:
    - processor.py - Main processing logic
    - config.py - Redis connection settings
    - database.py - Database connection for status updates

HOW TO RUN:
    python worker.py

QUEUE STRUCTURE:
    Queue name: 'lahstats:processing'
    Job payload: {'session_id': 'uuid', 'queued_at': 'timestamp'}
"""

import json
import logging
import time
import signal
import sys
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime

import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from config import settings
from processor import process_session_sync
from database import SessionLocal
from models import Session as SessionModel

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG,  # Verbose logging for detailed insights
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Queue names
PROCESSING_QUEUE = "lahstats:processing"
FAILED_QUEUE = "lahstats:failed"

# Worker settings
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5  # seconds (will be: 5s, 10s, 20s)
SHUTDOWN_TIMEOUT = 30  # seconds to wait for current job before forcing shutdown
REDIS_TIMEOUT = 1  # seconds for blocking pop timeout (to check shutdown flag)

# Global shutdown flag
shutdown_requested = False

# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

def signal_handler(signum, frame):
    """
    Handle shutdown signals gracefully.
    
    Allows current job to complete before shutting down.
    Triggered by SIGTERM (docker stop) or SIGINT (Ctrl+C).
    """
    global shutdown_requested
    signal_names = {
        signal.SIGTERM: "SIGTERM",
        signal.SIGINT: "SIGINT"
    }
    signal_name = signal_names.get(signum, str(signum))
    
    logger.info(f"📥 Received {signal_name}, initiating graceful shutdown...")
    logger.info("⏳ Waiting for current job to complete...")
    shutdown_requested = True


# ============================================================================
# JOB PROCESSING
# ============================================================================

def update_session_failure(session_id: str, error_message: str) -> None:
    """
    Update session status to 'failed' in database.
    
    Args:
        session_id: Session UUID as string
        error_message: Error description
    """
    logger.debug(f"Updating session {session_id} to failed status...")
    
    try:
        db = SessionLocal()
        session = db.query(SessionModel).filter(
            SessionModel.id == UUID(session_id)
        ).first()
        
        if session:
            session.status = "failed"
            session.error_message = error_message[:500]  # Truncate if too long
            db.commit()
            logger.info(f"📝 Updated session {session_id} status to 'failed'")
            logger.debug(f"   Error message: {error_message[:100]}")
        else:
            logger.warning(f"⚠️  Session {session_id} not found in database")
        
        db.close()
    except Exception as e:
        logger.error(f"❌ Failed to update session status in DB: {e}", exc_info=True)


def process_job(job_data: Dict, redis_client: redis.Redis) -> bool:
    """
    Process a single job with retry logic.
    
    Args:
        job_data: Job payload containing session_id
        redis_client: Redis client for pushing to failed queue
        
    Returns:
        True if successful, False if failed after all retries
    """
    session_id = job_data.get("session_id")
    queued_at = job_data.get("queued_at", "unknown")
    
    if not session_id:
        logger.error("❌ Job missing 'session_id' field")
        logger.debug(f"   Job data: {job_data}")
        return False
    
    logger.info("=" * 70)
    logger.info(f"🎬 Processing session: {session_id}")
    logger.info(f"   Queued at: {queued_at}")
    logger.debug(f"   Full job data: {job_data}")
    logger.info("-" * 70)
    
    # Retry loop with exponential backoff
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"Starting attempt {attempt}/{MAX_RETRIES}...")
            
            # Run the processing pipeline
            start_time = time.time()
            logger.debug("Calling process_session_sync()...")
            result = process_session_sync(UUID(session_id))
            elapsed = time.time() - start_time
            
            # Success!
            logger.info("✅ " + "=" * 68)
            logger.info(f"✅ Session {session_id} completed successfully!")
            logger.info(f"✅ Duration: {elapsed:.1f}s")
            logger.info(f"✅ Speakers: {result.get('speakers', 0)}")
            logger.info(f"✅ Segments: {result.get('segments', 0)}")
            logger.info(f"✅ Total words: {result.get('total_words', 0)}")
            logger.debug(f"✅ Full result: {result}")
            logger.info("✅ " + "=" * 68)
            
            return True
            
        except Exception as e:
            last_error = e
            error_msg = str(e)
            
            logger.error(f"❌ Attempt {attempt}/{MAX_RETRIES} failed")
            logger.error(f"❌ Error: {error_msg}")
            logger.debug(f"❌ Exception type: {type(e).__name__}", exc_info=True)
            
            if attempt < MAX_RETRIES:
                # Exponential backoff: 5s, 10s, 20s
                delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
                logger.info(f"⏳ Retrying in {delay} seconds...")
                logger.debug(f"   Next attempt will be {attempt + 1}/{MAX_RETRIES}")
                time.sleep(delay)
            else:
                # Final failure after all retries
                logger.error("=" * 70)
                logger.error(f"💥 Job FAILED after {MAX_RETRIES} attempts")
                logger.error(f"💥 Session: {session_id}")
                logger.error(f"💥 Final error: {error_msg}")
                logger.debug(f"💥 Exception details:", exc_info=True)
                logger.error("=" * 70)
                
                # Update session status in database
                logger.debug("Marking session as failed in database...")
                update_session_failure(session_id, error_msg)
                
                return False
    
    return False


# ============================================================================
# MAIN WORKER LOOP
# ============================================================================

def main():
    """
    Main worker loop.
    
    Connects to Redis queue and processes jobs until shutdown.
    Handles connection errors and implements graceful shutdown.
    """
    # Register signal handlers
    logger.debug("Registering signal handlers...")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Banner
    logger.info("=" * 70)
    logger.info("🚀 LahStats ML Processing Worker")
    logger.info("=" * 70)
    logger.info(f"📋 Processing Queue: {PROCESSING_QUEUE}")
    logger.info(f"📋 Failed Queue: {FAILED_QUEUE}")
    logger.info(f"🔄 Max Retries: {MAX_RETRIES}")
    logger.info(f"⏱️  Retry Delays: {RETRY_DELAY_BASE}s, {RETRY_DELAY_BASE*2}s, {RETRY_DELAY_BASE*4}s")
    logger.info(f"🔌 Redis URL: {settings.REDIS_URL}")
    logger.debug(f"🔧 Redis Timeout: {REDIS_TIMEOUT}s")
    logger.debug(f"🔧 Shutdown Timeout: {SHUTDOWN_TIMEOUT}s")
    logger.info("=" * 70)
    
    # Connect to Redis
    logger.debug("Initializing Redis connection...")
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30
        )
        
        # Test connection
        logger.debug("Testing Redis connection with PING...")
        redis_client.ping()
        logger.info("✅ Redis connection established")
        logger.debug(f"   Connection info: {redis_client.connection_pool}")
        logger.info("👂 Listening for jobs... (Press Ctrl+C to stop)")
        logger.info("-" * 70)
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}", exc_info=True)
        logger.error(f"💡 Make sure Redis is running: redis-server")
        logger.error(f"💡 Or start with Docker: docker run -d -p 6379:6379 redis:latest")
        sys.exit(1)
    
    # Job processing statistics
    jobs_processed = 0
    jobs_succeeded = 0
    jobs_failed = 0
    worker_start_time = time.time()
    
    logger.debug("Entering main processing loop...")
    
    # Main processing loop
    while not shutdown_requested:
        try:
            logger.debug(f"Waiting for job from queue '{PROCESSING_QUEUE}'...")
            
            # Blocking pop with timeout (allows checking shutdown flag)
            result = redis_client.brpop(PROCESSING_QUEUE, timeout=REDIS_TIMEOUT)
            
            if result is None:
                # Timeout - no job available, check shutdown and continue
                logger.debug("No job available (timeout), continuing...")
                continue
            
            _, job_data_str = result
            jobs_processed += 1
            
            logger.debug(f"Received job #{jobs_processed}")
            logger.debug(f"Raw job data: {job_data_str}")
            
            # Parse job data
            try:
                job_data = json.loads(job_data_str)
                logger.debug(f"Parsed job data: {job_data}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in job: {e}")
                logger.error(f"   Raw data: {job_data_str[:100]}")
                # Move to failed queue for inspection
                logger.debug(f"Moving invalid job to {FAILED_QUEUE}...")
                redis_client.lpush(FAILED_QUEUE, job_data_str)
                jobs_failed += 1
                continue
            
            # Process the job
            logger.debug("Calling process_job()...")
            success = process_job(job_data, redis_client)
            
            if success:
                jobs_succeeded += 1
                logger.debug(f"Job succeeded. Total successes: {jobs_succeeded}")
            else:
                jobs_failed += 1
                # Move failed job to failed queue for inspection/retry
                logger.debug(f"Moving failed job to {FAILED_QUEUE}...")
                redis_client.lpush(FAILED_QUEUE, job_data_str)
                logger.warning(f"📦 Job moved to failed queue: {FAILED_QUEUE}")
            
            # Calculate uptime
            uptime_seconds = int(time.time() - worker_start_time)
            uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
            
            logger.info(f"📊 Stats: {jobs_succeeded} succeeded, {jobs_failed} failed, {jobs_processed} total")
            logger.debug(f"📊 Uptime: {uptime_str}")
            logger.info("")
            
        except RedisConnectionError as e:
            logger.error(f"❌ Redis connection lost: {e}")
            logger.info("🔄 Attempting to reconnect in 5 seconds...")
            logger.debug("Connection error details:", exc_info=True)
            time.sleep(5)
            
            try:
                logger.debug("Reconnecting to Redis...")
                redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30
                )
                redis_client.ping()
                logger.info("✅ Reconnected to Redis")
            except Exception as reconnect_error:
                logger.error(f"❌ Reconnection failed: {reconnect_error}", exc_info=True)
            
        except KeyboardInterrupt:
            logger.info("⌨️  Keyboard interrupt received")
            break
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in worker loop: {e}", exc_info=True)
            logger.debug("Pausing for 1 second before continuing...")
            time.sleep(1)  # Brief pause before continuing
    
    # Shutdown summary
    uptime_seconds = int(time.time() - worker_start_time)
    uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("🛑 Worker Shutdown Complete")
    logger.info("=" * 70)
    logger.info(f"📊 Final Stats:")
    logger.info(f"   Total Jobs: {jobs_processed}")
    logger.info(f"   Succeeded: {jobs_succeeded}")
    logger.info(f"   Failed: {jobs_failed}")
    logger.info(f"   Uptime: {uptime_str}")
    logger.debug(f"   Success Rate: {(jobs_succeeded / jobs_processed * 100) if jobs_processed > 0 else 0:.1f}%")
    logger.info("=" * 70)
    
    logger.debug("Worker exiting with code 0")
    sys.exit(0)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.debug("Worker script starting...")
    main()
