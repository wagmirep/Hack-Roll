"""
tests/test_sessions.py - Session Endpoint Tests

PURPOSE:
    Test all session-related API endpoints.
    Covers session lifecycle from creation to claiming.

RESPONSIBILITIES:
    - Test POST /sessions/start
    - Test POST /sessions/{id}/upload
    - Test POST /sessions/{id}/end
    - Test GET /sessions/{id}/status
    - Test GET /sessions/{id}/speakers
    - Test POST /sessions/{id}/claim

REFERENCED BY:
    - pytest (test discovery)
    - CI/CD pipeline

REFERENCES:
    - conftest.py - Test fixtures
    - routers/sessions.py - Endpoints under test
    - schemas.py - Request/response schemas

TEST CASES:
    test_create_session_success:
        - Valid group_id and started_by
        - Returns session with status 'recording'

    test_create_session_invalid_group:
        - Invalid group_id format
        - Returns 422 validation error

    test_upload_chunk_success:
        - Valid session and audio file
        - Returns chunk number

    test_upload_chunk_invalid_session:
        - Non-existent session ID
        - Returns 404

    test_end_session_triggers_processing:
        - End active session
        - Status changes to 'processing'
        - Job queued in Redis

    test_get_status_during_processing:
        - Poll status endpoint
        - Returns progress percentage

    test_get_speakers_after_processing:
        - Session completed processing
        - Returns speaker list with samples

    test_claim_speaker_success:
        - Valid speaker and user
        - Speaker marked as claimed

    test_claim_already_claimed_speaker:
        - Speaker already claimed
        - Returns error
"""
