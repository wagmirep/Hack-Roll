"""
routers/sessions.py - Session Management Endpoints

PURPOSE:
    Define all API endpoints related to recording sessions.
    Handles session lifecycle from start to claiming completion.

RESPONSIBILITIES:
    - POST /sessions/start - Create new recording session
    - POST /sessions/{id}/upload - Upload audio chunk
    - POST /sessions/{id}/end - End session and trigger processing
    - GET /sessions/{id}/status - Get processing status and progress
    - GET /sessions/{id}/speakers - Get speakers for claiming
    - POST /sessions/{id}/claim - Claim a speaker identity

REFERENCED BY:
    - main.py - Included as router with prefix "/sessions"

REFERENCES:
    - models.py - Session, SessionSpeaker models
    - schemas.py - Request/response schemas
    - database.py - get_db() dependency
    - storage.py - Audio chunk upload
    - worker.py - Queue processing job (via Redis)
    - services/firebase.py - Real-time status updates

ENDPOINTS:
    POST /start
        Request: {group_id: UUID, started_by: UUID}
        Response: {id: UUID, status: 'recording', started_at: timestamp}

    POST /{session_id}/upload
        Request: multipart/form-data with audio file
        Response: {chunk_number: int, uploaded: true}

    POST /{session_id}/end
        Request: {}
        Response: {status: 'processing', message: 'Processing started'}

    GET /{session_id}/status
        Response: {status: string, progress: int, message: string}

    GET /{session_id}/speakers
        Response: {speakers: [{speaker_id, total_words, sample_audio_url, claimed_by}]}

    POST /{session_id}/claim
        Request: {speaker_id: string, user_id: UUID}
        Response: {success: bool, message: string}
"""
