"""
routers/groups.py - Group Statistics Endpoints

PURPOSE:
    Define API endpoints for group-level statistics and leaderboards.
    Aggregates word counts across sessions for group members.

RESPONSIBILITIES:
    - GET /groups/{id}/stats - Get group statistics
    - GET /groups/{id}/leaderboard - Get word leaderboard
    - GET /groups/{id}/wrapped - Get Spotify Wrapped-style stats

REFERENCED BY:
    - main.py - Included as router with prefix "/groups"

REFERENCES:
    - models.py - WordCount, Group models
    - schemas.py - Response schemas
    - database.py - get_db() dependency
    - services/firebase.py - Sync stats to Firebase

ENDPOINTS:
    GET /{group_id}/stats
        Response: {
            user_stats: {
                user_id: {walao: 10, lah: 15, ...},
                ...
            },
            total_sessions: int,
            date_range: {start: date, end: date}
        }

    GET /{group_id}/leaderboard
        Query params: ?word=walao&period=week
        Response: {
            word: string,
            rankings: [{user_id, count, rank}, ...]
        }

    GET /{group_id}/wrapped
        Query params: ?user_id=uuid&period=year
        Response: {
            top_words: [{word, count}, ...],
            total_words: int,
            favorite_word: string,
            percentile: int,
            fun_facts: [...]
        }
"""
