"""
schemas.py - Pydantic Request/Response Schemas

PURPOSE:
    Define Pydantic models for API request validation and response serialization.
    These schemas ensure type safety and automatic documentation.

RESPONSIBILITIES:
    - Define request schemas for all endpoints
    - Define response schemas for all endpoints
    - Provide validation rules (e.g., UUID format, required fields)
    - Generate OpenAPI documentation automatically

REFERENCED BY:
    - routers/sessions.py - Request/response validation
    - routers/groups.py - Request/response validation
    - main.py - OpenAPI schema generation

REFERENCES:
    - models.py - Mirrors database model structure

SCHEMAS:
    Requests:
        - SessionStartRequest: {group_id, started_by}
        - SessionEndRequest: {session_id}
        - ClaimSpeakerRequest: {speaker_id, user_id}

    Responses:
        - SessionResponse: {id, status, progress, started_at, ended_at}
        - SessionStatusResponse: {status, progress, message}
        - SpeakerResponse: {speaker_id, total_words, sample_audio_url, claimed_by}
        - SpeakersListResponse: {speakers: List[SpeakerResponse]}
        - ClaimResponse: {success, message}
        - GroupStatsResponse: {user_stats: Dict[user_id, word_counts], leaderboard}
        - WordCountResponse: {word, count}
"""
