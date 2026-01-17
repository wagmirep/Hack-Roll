# LahStats Backend API

FastAPI backend for LahStats - Singlish word tracking with speaker diarization.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
alembic upgrade head

# Start API server
uvicorn main:app --reload --port 8000

# Run processing worker (separate terminal)
python worker.py
```

## Architecture

- **main.py** - FastAPI app with REST endpoints
- **processor.py** - Background audio processing worker
- **models.py** - Database models (SQLAlchemy)
- **database.py** - Database connection setup
- **storage.py** - S3/cloud storage utilities

## API Endpoints

- `POST /sessions/start` - Create recording session
- `POST /sessions/{id}/upload` - Upload audio chunks
- `POST /sessions/{id}/end` - Stop & trigger processing
- `GET /sessions/{id}/status` - Poll processing progress
- `GET /sessions/{id}/speakers` - Get claiming data
- `POST /sessions/{id}/claim` - User claims speaker
- `GET /groups/{id}/stats` - Group statistics

## Models Used

- **MERaLiON-2-10B-ASR** - Singlish speech-to-text
- **pyannote/speaker-diarization-3.1** - Speaker segmentation
