# LahStats API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### Session Management

#### POST /sessions/start
Create a new recording session.

**Request:**
```json
{
  "group_id": "uuid",
  "started_by": "uuid"
}
```

**Response:**
```json
{
  "id": "session-uuid",
  "group_id": "uuid",
  "status": "recording",
  "started_at": "2025-01-15T12:00:00Z"
}
```

#### POST /sessions/{id}/upload
Upload audio chunks (every 30 seconds).

**Request:**
- Content-Type: multipart/form-data
- Field: `audio_chunk` (WAV file, 16kHz mono)

**Response:**
```json
{
  "chunk_number": 1,
  "uploaded_at": "2025-01-15T12:00:30Z"
}
```

#### POST /sessions/{id}/end
Stop recording and trigger processing.

**Response:**
```json
{
  "id": "session-uuid",
  "status": "processing",
  "ended_at": "2025-01-15T12:05:00Z"
}
```

#### GET /sessions/{id}/status
Poll processing progress.

**Response:**
```json
{
  "id": "session-uuid",
  "status": "processing",
  "progress": 75
}
```

### Speaker Claiming

#### GET /sessions/{id}/speakers
Get speaker data for claiming.

**Response:**
```json
{
  "speakers": [
    {
      "id": "uuid",
      "speaker_id": "SPEAKER_00",
      "sample_audio_url": "s3://...",
      "total_words": {
        "walao": 10,
        "lah": 15
      },
      "claimed_by": null
    }
  ]
}
```

#### POST /sessions/{id}/claim
User claims a speaker.

**Request:**
```json
{
  "speaker_id": "SPEAKER_00",
  "user_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "attributed_words": {
    "walao": 10,
    "lah": 15
  }
}
```

### Statistics

#### GET /groups/{id}/stats
Get group statistics.

**Query Parameters:**
- `period`: "daily", "weekly", "monthly"
- `user_id`: (optional) Filter for specific user

**Response:**
```json
{
  "group_id": "uuid",
  "period": "weekly",
  "stats": {
    "user-jeff": {
      "walao": 45,
      "lah": 120
    }
  },
  "leaderboard": [
    {"user_id": "user-jeff", "word": "lah", "count": 120}
  ]
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

**HTTP Status Codes:**
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error
