"""
models.py - SQLAlchemy Database Models

PURPOSE:
    Define all PostgreSQL database models using SQLAlchemy ORM.
    These models map directly to the Supabase database tables.
"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, ForeignKey, DECIMAL, UUID, JSON, Numeric, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


class Profile(Base):
    """User profile table - synced with Supabase auth.users"""
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    avatar_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    groups_created = relationship("Group", back_populates="creator", foreign_keys="Group.created_by")
    group_memberships = relationship("GroupMember", back_populates="user")
    sessions_started = relationship("Session", back_populates="starter")
    claimed_speakers = relationship("SessionSpeaker", back_populates="claimer", foreign_keys="SessionSpeaker.claimed_by")
    word_counts = relationship("WordCount", back_populates="user")


class Group(Base):
    """Group table - represents friend groups"""
    __tablename__ = "groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    invite_code = Column(String(10), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("Profile", back_populates="groups_created", foreign_keys=[created_by])
    members = relationship("GroupMember", back_populates="group")
    sessions = relationship("Session", back_populates="group")
    word_counts = relationship("WordCount", back_populates="group")


class GroupMember(Base):
    """Group membership table - many-to-many relationship"""
    __tablename__ = "group_members"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="members")
    user = relationship("Profile", back_populates="group_memberships")


class Session(Base):
    """Recording session table"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)
    started_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=False)
    status = Column(String(50), nullable=False, default="recording")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    progress = Column(Integer, default=0)
    audio_url = Column(Text)
    duration_seconds = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="sessions")
    starter = relationship("Profile", back_populates="sessions_started")
    speakers = relationship("SessionSpeaker", back_populates="session")
    word_counts = relationship("WordCount", back_populates="session")


class SessionSpeaker(Base):
    """Speaker detected in a session (with flexible claiming options)"""
    __tablename__ = "session_speakers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    speaker_label = Column(String(50), nullable=False)  # e.g., "SPEAKER_00"
    segment_count = Column(Integer, default=0)
    total_duration_seconds = Column(DECIMAL(10, 2))
    sample_audio_url = Column(Text)
    sample_start_time = Column(DECIMAL(10, 2))
    
    # Claiming fields
    claimed_by = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))  # Who performed the claim
    claimed_at = Column(DateTime(timezone=True))
    claim_type = Column(String(20))  # 'self', 'user', or 'guest'
    attributed_to_user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))  # For 'self' and 'user' types
    guest_name = Column(String(100))  # For 'guest' type
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="speakers")
    claimer = relationship("Profile", back_populates="claimed_speakers", foreign_keys=[claimed_by])
    attributed_to = relationship("Profile", foreign_keys=[attributed_to_user_id])
    word_counts = relationship("SpeakerWordCount", back_populates="speaker")


class SpeakerWordCount(Base):
    """Word counts for each speaker (before claiming)"""
    __tablename__ = "speaker_word_counts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_speaker_id = Column(UUID(as_uuid=True), ForeignKey("session_speakers.id", ondelete="CASCADE"), nullable=False)
    word = Column(String(50), nullable=False)
    count = Column(Integer, nullable=False, default=1)
    
    # Relationships
    speaker = relationship("SessionSpeaker", back_populates="word_counts")


class WordCount(Base):
    """Final word counts attributed to users (after claiming)"""
    __tablename__ = "word_counts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)  # Nullable for personal sessions
    word = Column(String(50), nullable=False)
    count = Column(Integer, nullable=False, default=1)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="word_counts")
    user = relationship("Profile", back_populates="word_counts")
    group = relationship("Group", back_populates="word_counts")


class TargetWord(Base):
    """Target Singlish words to track"""
    __tablename__ = "target_words"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    word = Column(String(50), unique=True, nullable=False)
    emoji = Column(String(10))
    category = Column(String(50))
    display_name = Column(String(50))
    is_active = Column(String, server_default='true')  # boolean stored as string in some DBs
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AudioChunk(Base):
    """Audio chunks uploaded during recording"""
    __tablename__ = "audio_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    chunk_number = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    duration_seconds = Column(DECIMAL(10, 2))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class ChunkTranscription(Base):
    """Cached transcription for uploaded audio chunks.

    Stores transcription results computed in the background as chunks are uploaded.
    Used by processor.py to speed up post-recording processing by reusing cached text.
    """
    __tablename__ = "chunk_transcriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    chunk_number = Column(Integer, nullable=False)

    # Transcription results
    raw_text = Column(Text, nullable=True)  # Raw model output
    corrected_text = Column(Text, nullable=True)  # After apply_corrections()
    word_counts = Column(JSONB, nullable=True)  # {word: count} dict

    # Metadata
    duration_seconds = Column(Numeric(10, 3), nullable=True)  # Chunk duration
    transcribed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)  # If transcription failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints - unique index on (session_id, chunk_number)
    __table_args__ = (
        Index('ix_chunk_transcriptions_session_chunk', 'session_id', 'chunk_number', unique=True),
    )
