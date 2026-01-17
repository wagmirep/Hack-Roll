"""
models.py - SQLAlchemy Database Models

PURPOSE:
    Define all PostgreSQL database models using SQLAlchemy ORM.
    These models map directly to the database tables.

RESPONSIBILITIES:
    - Define Session model (recording sessions)
    - Define SessionSpeaker model (speaker data before claiming)
    - Define WordCount model (final attributed word counts)
    - Define User model (if needed for auth)
    - Define Group model (user groups)

REFERENCED BY:
    - routers/sessions.py - CRUD operations on sessions
    - routers/groups.py - Group statistics queries
    - processor.py - Creating speaker records after processing
    - services/firebase.py - Syncing data to Firebase

REFERENCES:
    - database.py - Base model and engine

TABLES:
    sessions:
        - id: UUID PRIMARY KEY
        - group_id: UUID NOT NULL
        - started_by: UUID NOT NULL
        - started_at: TIMESTAMP NOT NULL
        - ended_at: TIMESTAMP
        - status: VARCHAR(50) ['recording', 'processing', 'ready_for_claiming', 'completed']
        - progress: INT DEFAULT 0

    session_speakers:
        - id: UUID PRIMARY KEY
        - session_id: UUID NOT NULL (FK -> sessions.id)
        - speaker_id: VARCHAR(50) ['SPEAKER_00', 'SPEAKER_01', ...]
        - total_words: JSONB {'walao': 10, 'lah': 15}
        - sample_audio_url: TEXT
        - segment_count: INT
        - claimed_by: UUID (NULL until claimed)
        - claimed_at: TIMESTAMP

    word_counts:
        - id: BIGSERIAL PRIMARY KEY
        - session_id: UUID NOT NULL
        - user_id: UUID NOT NULL
        - group_id: UUID NOT NULL
        - word: VARCHAR(50)
        - count: INT
        - detected_at: TIMESTAMP DEFAULT NOW()
"""
