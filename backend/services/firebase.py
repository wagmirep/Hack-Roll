"""
services/firebase.py - Firebase Realtime Database Service

PURPOSE:
    Handle all Firebase Realtime Database operations for live sync.
    Provides real-time updates to mobile clients.

RESPONSIBILITIES:
    - Initialize Firebase Admin SDK
    - Sync session status updates in real-time
    - Update group live word counts
    - Maintain leaderboard data
    - Track active sessions per group

REFERENCED BY:
    - processor.py - Update status during processing
    - routers/sessions.py - Update on session events
    - routers/groups.py - Sync group statistics

REFERENCES:
    - config.py - FIREBASE_PROJECT_ID, FIREBASE_CREDENTIALS

FIREBASE STRUCTURE:
    {
        "groups": {
            "{group_id}": {
                "live_counts": {
                    "{user_id}": {"walao": 10, "lah": 15, ...}
                },
                "leaderboard": [
                    {"user_id": "...", "total": 100, "rank": 1},
                    ...
                ],
                "active_session": "{session_id}" or null
            }
        },
        "sessions": {
            "{session_id}": {
                "status": "processing",
                "progress": 45,
                "updated_at": timestamp
            }
        }
    }

FUNCTIONS:
    - get_firebase_app() -> firebase_admin.App
        Returns initialized Firebase app instance

    - update_session_status(session_id, status, progress) -> None
        Update session processing status in real-time

    - update_group_counts(group_id, user_id, word_counts) -> None
        Add word counts to group live_counts

    - update_leaderboard(group_id) -> None
        Recalculate and update group leaderboard

    - set_active_session(group_id, session_id) -> None
        Mark session as active for group

    - clear_active_session(group_id) -> None
        Clear active session when complete
"""
