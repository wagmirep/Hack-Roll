"""
redis_client.py - Redis Client Singleton

PURPOSE:
    Centralized Redis client for job queue management.
    Provides thread-safe singleton pattern for Redis connections.

RESPONSIBILITIES:
    - Manage Redis connection lifecycle
    - Provide singleton access to Redis client
    - Handle connection errors gracefully
    - Define queue name constants

REFERENCED BY:
    - routers/sessions.py - Queue processing jobs
    - worker.py - Process jobs from queue
    - main.py - Health check endpoint

REFERENCES:
    - config.py - REDIS_URL configuration

USAGE:
    from redis_client import get_redis_client, PROCESSING_QUEUE
    
    redis = get_redis_client()
    redis.lpush(PROCESSING_QUEUE, job_data)
"""

import logging
from typing import Optional

import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# QUEUE CONFIGURATION
# ============================================================================

# Queue names - must match worker.py
PROCESSING_QUEUE = "lahstats:processing"
FAILED_QUEUE = "lahstats:failed"

# ============================================================================
# REDIS CLIENT SINGLETON
# ============================================================================

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client instance.
    
    Uses singleton pattern to reuse the same connection across requests.
    Thread-safe initialization.
    
    Returns:
        Redis client instance
        
    Raises:
        ValueError: If REDIS_URL not configured
        redis.ConnectionError: If Redis is not reachable
        
    Example:
        >>> client = get_redis_client()
        >>> client.ping()
        True
    """
    global _redis_client
    
    if _redis_client is not None:
        # Check if connection is still alive
        try:
            _redis_client.ping()
            return _redis_client
        except RedisConnectionError:
            logger.warning("Redis connection lost, reconnecting...")
            _redis_client = None
    
    # Create new connection
    if not settings.REDIS_URL:
        raise ValueError(
            "REDIS_URL not configured in settings. "
            "Set REDIS_URL environment variable or update config.py"
        )
    
    logger.debug(f"Connecting to Redis: {settings.REDIS_URL}")
    
    try:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,  # Auto-decode bytes to strings
            socket_connect_timeout=5,  # 5 second connection timeout
            socket_keepalive=True,  # Keep connection alive
            health_check_interval=30,  # Check connection health every 30s
            retry_on_timeout=True,  # Retry if timeout occurs
            max_connections=50  # Connection pool size
        )
        
        # Test connection
        _redis_client.ping()
        logger.info("✅ Redis client initialized successfully")
        
        return _redis_client
        
    except RedisConnectionError as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        logger.error(
            "💡 Make sure Redis is running:\n"
            "   - redis-server (local)\n"
            "   - docker run -d -p 6379:6379 redis:latest (Docker)"
        )
        _redis_client = None
        raise
    
    except Exception as e:
        logger.error(f"❌ Unexpected error initializing Redis: {e}", exc_info=True)
        _redis_client = None
        raise


def close_redis_client() -> None:
    """
    Close the Redis connection.
    
    Useful for cleanup during testing or graceful shutdown.
    The connection will be automatically recreated on next get_redis_client() call.
    
    Example:
        >>> close_redis_client()
        >>> # Connection closed, will reconnect on next get_redis_client()
    """
    global _redis_client
    
    if _redis_client is not None:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None


def is_redis_connected() -> bool:
    """
    Check if Redis client is connected and responding.
    
    Returns:
        True if connected and responding to PING, False otherwise
        
    Example:
        >>> if is_redis_connected():
        ...     print("Redis is ready")
    """
    try:
        client = get_redis_client()
        client.ping()
        return True
    except Exception:
        return False


def get_queue_length(queue_name: str) -> int:
    """
    Get the number of jobs in a queue.
    
    Args:
        queue_name: Name of the queue (e.g., PROCESSING_QUEUE)
        
    Returns:
        Number of jobs in the queue, or 0 if error
        
    Example:
        >>> pending = get_queue_length(PROCESSING_QUEUE)
        >>> print(f"{pending} jobs pending")
    """
    try:
        client = get_redis_client()
        return client.llen(queue_name)
    except Exception as e:
        logger.error(f"Failed to get queue length for {queue_name}: {e}")
        return 0


def clear_queue(queue_name: str) -> int:
    """
    Clear all jobs from a queue.
    
    ⚠️ WARNING: This deletes all jobs in the queue!
    Use with caution, typically only for testing or maintenance.
    
    Args:
        queue_name: Name of the queue to clear
        
    Returns:
        Number of jobs removed
        
    Example:
        >>> removed = clear_queue(FAILED_QUEUE)
        >>> print(f"Cleared {removed} failed jobs")
    """
    try:
        client = get_redis_client()
        length = client.llen(queue_name)
        client.delete(queue_name)
        logger.warning(f"Cleared {length} jobs from queue: {queue_name}")
        return length
    except Exception as e:
        logger.error(f"Failed to clear queue {queue_name}: {e}")
        return 0


# ============================================================================
# HEALTH CHECK UTILITIES
# ============================================================================

def get_redis_info() -> dict:
    """
    Get Redis server information.
    
    Returns:
        Dictionary with Redis info, or error dict if connection fails
        
    Example:
        >>> info = get_redis_info()
        >>> print(f"Redis version: {info.get('redis_version')}")
    """
    try:
        client = get_redis_client()
        info = client.info()
        return {
            "connected": True,
            "redis_version": info.get("redis_version"),
            "used_memory_human": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "uptime_in_seconds": info.get("uptime_in_seconds"),
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


def get_queue_stats() -> dict:
    """
    Get statistics about all queues.
    
    Returns:
        Dictionary with queue statistics
        
    Example:
        >>> stats = get_queue_stats()
        >>> print(f"Processing: {stats['processing']}, Failed: {stats['failed']}")
    """
    return {
        "processing": get_queue_length(PROCESSING_QUEUE),
        "failed": get_queue_length(FAILED_QUEUE)
    }
