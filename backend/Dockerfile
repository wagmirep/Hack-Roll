# Dockerfile - LahStats Backend (Slim)
#
# Lightweight production container for FastAPI backend.
# ML models (transcription + diarization) run on Colab via external API.
# This image is ~500MB vs ~8GB with ML dependencies.

FROM python:3.11-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy slim requirements first for layer caching
COPY requirements-slim.txt .

# Install Python dependencies (no ML packages)
RUN pip install --no-cache-dir -r requirements-slim.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
