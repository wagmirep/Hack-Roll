# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- PostgreSQL database (RDS/Supabase)
- Redis instance
- S3-compatible storage
- Firebase project

## Backend Deployment

### 1. Environment Setup

```bash
# Production .env
DATABASE_URL=postgresql://user:pass@prod-host:5432/lahstats
REDIS_URL=redis://prod-redis:6379
S3_BUCKET=lahstats-audio-prod
AWS_ACCESS_KEY_ID=prod-key
AWS_SECRET_ACCESS_KEY=prod-secret
HUGGINGFACE_TOKEN=your-token
FIREBASE_CREDENTIALS=/app/firebase-creds.json
```

### 2. Database Migration

```bash
# Run migrations
alembic upgrade head

# Verify
psql $DATABASE_URL -c "\dt"
```

### 3. Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download models (optional: pre-bake into image)
RUN python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='MERaLiON/MERaLiON-2-10B-ASR')"

# Copy application
COPY . .

# Expose API port
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  worker:
    build: ./backend
    command: python worker.py
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

**Deploy:**
```bash
docker-compose up -d
```

## Mobile Deployment

### 1. Build for Production

**iOS:**
```bash
cd mobile
eas build --platform ios
```

**Android:**
```bash
eas build --platform android
```

### 2. Environment Configuration

Create production config:
```javascript
// app.config.js
export default {
  expo: {
    name: "LahStats",
    extra: {
      apiUrl: process.env.API_URL || "https://api.lahstats.com",
      firebaseConfig: JSON.parse(process.env.FIREBASE_CONFIG)
    }
  }
}
```

### 3. Publish Update

```bash
eas update --branch production
```

## Infrastructure

### Recommended Stack

**Hosting:**
- Backend: Railway / Render / AWS ECS
- Database: Supabase / AWS RDS
- Redis: Upstash / AWS ElastiCache
- Storage: AWS S3 / Cloudflare R2

**Cost Estimate (MVP):**
- Backend hosting: $10-20/month
- Database: Free (Supabase) - $25/month
- Redis: Free (Upstash) - $10/month
- S3: ~$5/month
- **Total:** ~$0-60/month

### Scaling Considerations

**Processing Worker:**
- Use GPU instances for faster processing
- Scale horizontally with Redis queue
- Typical: t3.medium + GPU for workers

**Database:**
- Index on `session_id`, `group_id`, `user_id`
- Partition `word_counts` by month

**Storage:**
- Lifecycle policy: Delete audio after 30 days
- Use CloudFront CDN for sample audio

## Monitoring

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "redis": check_redis(),
        "database": check_db(),
        "models": check_models_loaded()
    }
```

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Metrics

- Processing time per session
- Transcription accuracy (manual review)
- API response times
- Queue depth

## Security

1. **API Keys:** Use secrets manager (AWS Secrets Manager / Doppler)
2. **HTTPS:** Enforce TLS 1.3
3. **Rate Limiting:** 100 requests/minute per user
4. **CORS:** Whitelist mobile app origin
5. **Audio Storage:** Pre-signed URLs with 1-hour expiry

## Rollback Procedure

```bash
# Revert database migration
alembic downgrade -1

# Rollback Docker container
docker-compose down
docker-compose up -d --no-deps --build api

# Rollback mobile app
eas update --branch production --message "Rollback"
```

## Backup Strategy

**Database:**
```bash
# Daily backups
pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz
```

**Redis:**
- Persistent AOF enabled
- Daily RDB snapshots

**Audio Files:**
- S3 versioning enabled
- Cross-region replication

## Post-Deployment Checklist

- [ ] Health endpoint returns 200
- [ ] Database migrations applied
- [ ] Redis connection working
- [ ] S3 bucket accessible
- [ ] Firebase credentials valid
- [ ] HuggingFace token set
- [ ] Test audio upload → process → claim flow
- [ ] Mobile app can connect to API
- [ ] Monitoring/logging configured
