"""
schemas.py - Pydantic Request/Response Schemas

PURPOSE:
    Define Pydantic models for API request validation and response serialization.
    These schemas ensure type safety and automatic documentation.
"""

from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class ProfileResponse(BaseModel):
    """User profile response"""
    id: UUID4
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """Update user profile request"""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class MeResponse(BaseModel):
    """Response for /auth/me endpoint with profile and groups"""
    profile: ProfileResponse
    groups: List['GroupResponse'] = []


# ============================================================================
# GROUP SCHEMAS
# ============================================================================

class GroupCreateRequest(BaseModel):
    """Create new group request"""
    name: str = Field(..., min_length=1, max_length=100)


class GroupResponse(BaseModel):
    """Group details response"""
    id: UUID4
    name: str
    created_by: UUID4
    invite_code: str
    created_at: datetime
    member_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class GroupJoinRequest(BaseModel):
    """Join group with invite code request"""
    invite_code: str = Field(..., min_length=6, max_length=10)


class GroupMemberResponse(BaseModel):
    """Group member response"""
    id: UUID4
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    joined_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# SESSION SCHEMAS
# ============================================================================

class SessionCreateRequest(BaseModel):
    """Create new recording session request"""
    group_id: Optional[UUID4] = None


class SessionResponse(BaseModel):
    """Recording session response"""
    id: UUID4
    group_id: Optional[UUID4] = None
    started_by: UUID4
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    progress: int = 0
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class SessionEndRequest(BaseModel):
    """End recording session request"""
    final_duration_seconds: Optional[int] = None


class ChunkUploadResponse(BaseModel):
    """Chunk upload response"""
    chunk_number: int
    uploaded: bool
    storage_path: str


# ============================================================================
# SPEAKER SCHEMAS
# ============================================================================

class SpeakerWordCountResponse(BaseModel):
    """Word count for a speaker"""
    word: str
    count: int
    emoji: Optional[str] = None


class SpeakerResponse(BaseModel):
    """Speaker details for claiming"""
    id: UUID4
    speaker_label: str
    segment_count: int
    total_duration_seconds: Optional[Decimal] = None
    sample_audio_url: Optional[str] = None
    sample_start_time: Optional[Decimal] = None
    claimed_by: Optional[UUID4] = None
    claimed_at: Optional[datetime] = None
    claim_type: Optional[str] = None  # 'self', 'user', or 'guest'
    attributed_to_user_id: Optional[UUID4] = None
    guest_name: Optional[str] = None
    word_counts: List[SpeakerWordCountResponse] = []
    
    class Config:
        from_attributes = True


class SpeakersListResponse(BaseModel):
    """List of speakers in a session"""
    speakers: List[SpeakerResponse]


class ClaimSpeakerRequest(BaseModel):
    """Claim speaker identity request"""
    speaker_id: UUID4
    claim_type: str = Field(..., pattern="^(self|user|guest)$")  # Must be 'self', 'user', or 'guest'
    attributed_to_user_id: Optional[UUID4] = None  # Required for claim_type='user'
    guest_name: Optional[str] = Field(None, min_length=1, max_length=100)  # Required for claim_type='guest'


class ClaimSpeakerResponse(BaseModel):
    """Claim speaker response"""
    success: bool
    message: str
    speaker: Optional[SpeakerResponse] = None


# ============================================================================
# RESULTS SCHEMAS
# ============================================================================

class UserWordCountResponse(BaseModel):
    """User's word count for a specific word"""
    word: str
    count: int
    emoji: Optional[str] = None


class TopWordResponse(BaseModel):
    """Top word information"""
    word: str
    count: int


class UserResultResponse(BaseModel):
    """User's results in a session"""
    speaker_id: str  # Unique identifier for this speaker in the session
    user_id: Optional[UUID4] = None  # None for guest users
    username: Optional[str] = None
    name: Optional[str] = None  # Display name or guest name
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_guest: bool = False
    word_counts: List[UserWordCountResponse]
    total_words: int
    top_word: Optional[TopWordResponse] = None


class SessionResultsResponse(BaseModel):
    """Complete session results"""
    session_id: UUID4
    status: str
    duration_seconds: int
    total_words: int
    total_singlish_words: int
    speakers: List[UserResultResponse]  # Renamed from users for frontend compatibility
    all_claimed: bool


class SessionHistoryResponse(BaseModel):
    """Session history with summary stats"""
    id: UUID4
    group_id: Optional[UUID4] = None
    started_by: UUID4
    started_by_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_speakers: int = 0
    my_total_words: int = 0
    group_total_words: int = 0


class UserSessionStatsResponse(BaseModel):
    """Individual user stats for a specific session"""
    session_id: UUID4
    user_id: UUID4
    username: str
    display_name: Optional[str]
    word_counts: List[UserWordCountResponse]
    total_words: int
    session_started_at: datetime
    session_duration: Optional[int]


class SessionComparisonItem(BaseModel):
    """Stats for one session in comparison"""
    session_id: UUID4
    started_at: datetime
    total_words: int
    unique_words: int
    word_counts: List[UserWordCountResponse]


class SessionComparisonResponse(BaseModel):
    """Compare multiple sessions"""
    user_id: UUID4
    sessions: List[SessionComparisonItem]
    total_across_sessions: int
    average_per_session: float


# ============================================================================
# USER SEARCH SCHEMAS
# ============================================================================

class UserSearchResult(BaseModel):
    """User search result for tagging speakers"""
    id: UUID4
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserSearchResponse(BaseModel):
    """User search response"""
    users: List[UserSearchResult]
    total: int


# ============================================================================
# STATS SCHEMAS
# ============================================================================

class WordStatsResponse(BaseModel):
    """Word statistics"""
    word: str
    count: int
    emoji: Optional[str] = None


class UserStatsResponse(BaseModel):
    """User statistics"""
    user_id: UUID4
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    word_counts: List[WordStatsResponse]
    total_words: int
    rank: Optional[int] = None
    top_words: Optional[Dict[str, int]] = None  # Dictionary mapping word to count for frontend compatibility


class GroupStatsResponse(BaseModel):
    """Group statistics"""
    group_id: UUID4
    group_name: str
    period: str
    total_sessions: int
    total_words: int
    leaderboard: List[UserStatsResponse]
    word_breakdown: List[WordStatsResponse]


class GlobalLeaderboardResponse(BaseModel):
    """Global leaderboard across all users"""
    period: str
    total_users: int
    total_sessions: int
    total_words: int
    leaderboard: List[UserStatsResponse]
    top_words: List[WordStatsResponse]


class MyStatsResponse(BaseModel):
    """Current user's personal statistics"""
    user_id: UUID4
    period: str
    total_words: int
    total_sessions: int
    word_counts: List[WordStatsResponse]
    favorite_word: Optional[str] = None
    groups: List[Dict] = []


# ============================================================================
# WRAPPED SCHEMAS
# ============================================================================

class WrappedResponse(BaseModel):
    """Spotify Wrapped-style year recap"""
    user_id: UUID4
    year: int
    total_words: int
    total_sessions: int
    top_words: List[WordStatsResponse]
    favorite_word: str
    percentile: int
    fun_facts: List[str]
    personality: str
    badges: List[str]


class TrendDataPoint(BaseModel):
    """Single data point in trends analysis"""
    period: datetime
    total_words: int
    sessions: int


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============================================================================
# HEALTH CHECK SCHEMAS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    version: str


# ============================================================================
# MODEL REBUILDING FOR FORWARD REFERENCES
# ============================================================================

# Rebuild models that use forward references
MeResponse.model_rebuild()
