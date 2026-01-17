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
    Job payload: {'session_id': 'uuid', 'started_at': 'timestamp'}
"""
