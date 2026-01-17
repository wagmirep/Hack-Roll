"""
routers/sessions.py - Session Management Endpoints

PURPOSE:
    Define all API endpoints related to recording sessions.
    Handles session lifecycle from start to claiming completion.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from auth import get_current_user
from models import (
    Session as SessionModel, SessionSpeaker, SpeakerWordCount,
    WordCount, GroupMember, Profile, TargetWord, AudioChunk
)
from schemas import (
    SessionCreateRequest, SessionResponse, SessionEndRequest,
    ChunkUploadResponse, SpeakersListResponse, SpeakerResponse,
    ClaimSpeakerRequest, ClaimSpeakerResponse, SessionResultsResponse,
    UserResultResponse, UserWordCountResponse, SpeakerWordCountResponse,
    SessionHistoryResponse, UserSessionStatsResponse, SessionComparisonResponse
)
from storage import storage
import uuid
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=List[SessionHistoryResponse])
async def list_sessions(
    group_id: Optional[uuid.UUID] = Query(None, description="Filter by group"),
    status: Optional[str] = Query(None, regex="^(recording|processing|ready_for_claiming|completed|failed)$"),
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get session history with filters and pagination.
    Shows sessions the user has access to (their groups).
    
    Args:
        group_id: Optional filter by specific group
        status: Optional filter by session status
        limit: Max number of results (default 20, max 100)
        offset: Pagination offset
        
    Returns:
        List of sessions with summary stats
    """
    # Build base query - only sessions from groups user is in
    query = db.query(SessionModel).join(
        GroupMember,
        GroupMember.group_id == SessionModel.group_id
    ).filter(
        GroupMember.user_id == current_user.id
    )
    
    # Apply filters
    if group_id:
        query = query.filter(SessionModel.group_id == group_id)
    
    if status:
        query = query.filter(SessionModel.status == status)
    
    # Order by most recent first
    query = query.order_by(desc(SessionModel.started_at))
    
    # Apply pagination
    sessions = query.offset(offset).limit(limit).all()
    
    # Build response with stats
    result = []
    for session in sessions:
        # Get starter name
        starter = db.query(Profile).filter(Profile.id == session.started_by).first()
        
        # Count total speakers
        total_speakers = db.query(SessionSpeaker).filter(
            SessionSpeaker.session_id == session.id
        ).count()
        
        # Get my word count for this session
        my_words = db.query(func.sum(WordCount.count)).filter(
            WordCount.session_id == session.id,
            WordCount.user_id == current_user.id
        ).scalar() or 0
        
        # Get group total for this session
        group_words = db.query(func.sum(WordCount.count)).filter(
            WordCount.session_id == session.id
        ).scalar() or 0
        
        result.append(SessionHistoryResponse(
            id=session.id,
            group_id=session.group_id,
            started_by=session.started_by,
            started_by_name=starter.display_name or starter.username if starter else "Unknown",
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_seconds=session.duration_seconds,
            total_speakers=total_speakers,
            my_total_words=my_words,
            group_total_words=group_words
        ))
    
    return result


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new recording session.
    
    Args:
        request: Session creation details
        
    Returns:
        Created session
    """
    # Verify user is member of group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == request.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this group"
        )
    
    # Create session
    session = SessionModel(
        group_id=request.group_id,
        started_by=current_user.id,
        status="recording"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session


@router.post("/{session_id}/chunks", response_model=ChunkUploadResponse)
async def upload_chunk(
    session_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an audio chunk for a session.
    
    Args:
        session_id: Session ID
        file: Audio file chunk
        
    Returns:
        Upload confirmation
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user is in the group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == session.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload to this session"
        )
    
    # Get next chunk number
    chunk_count = db.query(AudioChunk).filter(
        AudioChunk.session_id == session_id
    ).count()
    chunk_number = chunk_count + 1
    
    # Upload to storage
    storage_path = await storage.upload_chunk(session_id, chunk_number, file)
    
    # Save chunk record
    chunk = AudioChunk(
        session_id=session_id,
        chunk_number=chunk_number,
        storage_path=storage_path
    )
    db.add(chunk)
    db.commit()
    
    return ChunkUploadResponse(
        chunk_number=chunk_number,
        uploaded=True,
        storage_path=storage_path
    )


@router.post("/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: uuid.UUID,
    request: SessionEndRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End a recording session and trigger processing.
    
    Args:
        session_id: Session ID
        request: End session details
        
    Returns:
        Updated session
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user started the session or is in the group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == session.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Update session
    session.ended_at = datetime.utcnow()
    session.status = "processing"
    session.progress = 0
    
    if request.final_duration_seconds:
        session.duration_seconds = request.final_duration_seconds
    
    db.commit()
    db.refresh(session)
    
    # TODO: Queue background processing job
    # For now, we'll create mock speakers for testing
    
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session_status(
    session_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get session status and progress.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session details
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user is in the group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == session.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return session


@router.get("/{session_id}/speakers", response_model=SpeakersListResponse)
async def get_session_speakers(
    session_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get speakers for claiming.
    
    Args:
        session_id: Session ID
        
    Returns:
        List of speakers with word counts
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user is in the group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == session.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get speakers with word counts
    speakers = db.query(SessionSpeaker).filter(
        SessionSpeaker.session_id == session_id
    ).all()
    
    # Get target words with emojis
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    result = []
    for speaker in speakers:
        # Get word counts for this speaker
        word_counts_query = db.query(SpeakerWordCount).filter(
            SpeakerWordCount.session_speaker_id == speaker.id
        ).all()
        
        word_counts = [
            SpeakerWordCountResponse(
                word=wc.word,
                count=wc.count,
                emoji=target_words.get(wc.word)
            )
            for wc in word_counts_query
        ]
        
        speaker_response = SpeakerResponse(
            id=speaker.id,
            speaker_label=speaker.speaker_label,
            segment_count=speaker.segment_count,
            total_duration_seconds=speaker.total_duration_seconds,
            sample_audio_url=speaker.sample_audio_url,
            sample_start_time=speaker.sample_start_time,
            claimed_by=speaker.claimed_by,
            claimed_at=speaker.claimed_at,
            word_counts=word_counts
        )
        result.append(speaker_response)
    
    return SpeakersListResponse(speakers=result)


@router.post("/{session_id}/claim", response_model=ClaimSpeakerResponse)
async def claim_speaker(
    session_id: uuid.UUID,
    request: ClaimSpeakerRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Claim a speaker identity with three modes:
    - 'self': Claim speaker as yourself
    - 'user': Tag speaker as another registered user (requires attributed_to_user_id)
    - 'guest': Tag speaker as a guest participant (requires guest_name)
    
    Args:
        session_id: Session ID
        request: Speaker to claim with claim type
        
    Returns:
        Claim confirmation
    """
    # Validate request based on claim_type
    if request.claim_type == 'user' and not request.attributed_to_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="attributed_to_user_id is required for claim_type='user'"
        )
    
    if request.claim_type == 'guest' and not request.guest_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="guest_name is required for claim_type='guest'"
        )
    
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user is in the group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == session.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get speaker
    speaker = db.query(SessionSpeaker).filter(
        SessionSpeaker.id == request.speaker_id,
        SessionSpeaker.session_id == session_id
    ).first()
    
    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Speaker not found"
        )
    
    # Check if already claimed
    if speaker.claimed_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Speaker already claimed"
        )
    
    # For 'user' claim type, verify the attributed user exists and is in the group
    if request.claim_type == 'user':
        attributed_user = db.query(Profile).filter(
            Profile.id == request.attributed_to_user_id
        ).first()
        
        if not attributed_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attributed user not found"
            )
        
        # Check if attributed user is in the group
        attributed_member = db.query(GroupMember).filter(
            GroupMember.group_id == session.group_id,
            GroupMember.user_id == request.attributed_to_user_id
        ).first()
        
        if not attributed_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attributed user is not a member of this group"
            )
    
    # Update speaker with claim information
    speaker.claimed_by = current_user.id
    speaker.claimed_at = datetime.utcnow()
    speaker.claim_type = request.claim_type
    
    if request.claim_type == 'self':
        speaker.attributed_to_user_id = current_user.id
    elif request.claim_type == 'user':
        speaker.attributed_to_user_id = request.attributed_to_user_id
    elif request.claim_type == 'guest':
        speaker.guest_name = request.guest_name
        speaker.attributed_to_user_id = None
    
    # Create word count records only for 'self' and 'user' claim types
    # For 'guest', stats remain in speaker_word_counts only
    if request.claim_type in ['self', 'user']:
        target_user_id = speaker.attributed_to_user_id
        
        speaker_word_counts = db.query(SpeakerWordCount).filter(
            SpeakerWordCount.session_speaker_id == speaker.id
        ).all()
        
        for swc in speaker_word_counts:
            word_count = WordCount(
                session_id=session_id,
                user_id=target_user_id,
                group_id=session.group_id,
                word=swc.word,
                count=swc.count
            )
            db.add(word_count)
    
    db.commit()
    db.refresh(speaker)
    
    # Check if all speakers are claimed
    unclaimed = db.query(SessionSpeaker).filter(
        SessionSpeaker.session_id == session_id,
        SessionSpeaker.claimed_by == None
    ).count()
    
    if unclaimed == 0:
        session.status = "completed"
        db.commit()
    
    claim_message = {
        'self': 'Speaker claimed as yourself',
        'user': f'Speaker tagged to user',
        'guest': f'Speaker tagged as guest: {request.guest_name}'
    }
    
    return ClaimSpeakerResponse(
        success=True,
        message=claim_message[request.claim_type]
    )


@router.get("/{session_id}/results", response_model=SessionResultsResponse)
async def get_session_results(
    session_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get final session results after all speakers are claimed.
    Includes registered users (self/user claims) and guest participants.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session results with all user and guest word counts
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user is in the group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == session.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get target words with emojis
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    # Get word counts by registered users (from word_counts table)
    word_counts = db.query(WordCount).filter(
        WordCount.session_id == session_id
    ).all()
    
    # Organize by user
    user_stats = {}
    for wc in word_counts:
        if wc.user_id not in user_stats:
            user_stats[wc.user_id] = {
                "word_counts": {},
                "total": 0
            }
        user_stats[wc.user_id]["word_counts"][wc.word] = wc.count
        user_stats[wc.user_id]["total"] += wc.count
    
    # Build registered user results
    users = []
    for user_id, stats in user_stats.items():
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if profile:
            word_count_list = [
                UserWordCountResponse(
                    word=word,
                    count=count,
                    emoji=target_words.get(word)
                )
                for word, count in stats["word_counts"].items()
            ]
            
            users.append(UserResultResponse(
                user_id=profile.id,
                username=profile.username,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                is_guest=False,
                word_counts=word_count_list,
                total_words=stats["total"]
            ))
    
    # Get guest speakers (claim_type='guest')
    guest_speakers = db.query(SessionSpeaker).filter(
        SessionSpeaker.session_id == session_id,
        SessionSpeaker.claim_type == 'guest'
    ).all()
    
    # Build guest results
    for guest_speaker in guest_speakers:
        # Get word counts from speaker_word_counts table
        guest_word_counts = db.query(SpeakerWordCount).filter(
            SpeakerWordCount.session_speaker_id == guest_speaker.id
        ).all()
        
        word_count_list = [
            UserWordCountResponse(
                word=wc.word,
                count=wc.count,
                emoji=target_words.get(wc.word)
            )
            for wc in guest_word_counts
        ]
        
        total_words = sum(wc.count for wc in guest_word_counts)
        
        users.append(UserResultResponse(
            user_id=None,
            username=None,
            display_name=guest_speaker.guest_name,
            avatar_url=None,
            is_guest=True,
            word_counts=word_count_list,
            total_words=total_words
        ))
    
    # Check if all speakers are claimed
    all_claimed = db.query(SessionSpeaker).filter(
        SessionSpeaker.session_id == session_id,
        SessionSpeaker.claimed_by == None
    ).count() == 0
    
    return SessionResultsResponse(
        session_id=session_id,
        status=session.status,
        users=users,
        all_claimed=all_claimed
    )


@router.get("/{session_id}/my-stats", response_model=UserSessionStatsResponse)
async def get_my_session_stats(
    session_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get my personal stats for a specific session.
    Shows what I said in a particular recording session.
    
    Args:
        session_id: Session ID
        
    Returns:
        User's word counts for that session
    """
    # Get session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user is in the group
    member = db.query(GroupMember).filter(
        GroupMember.group_id == session.group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get target words for emoji mapping
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    # Get my word counts for this session
    word_counts = db.query(WordCount).filter(
        WordCount.session_id == session_id,
        WordCount.user_id == current_user.id
    ).all()
    
    # Build word count list
    word_count_list = [
        UserWordCountResponse(
            word=wc.word,
            count=wc.count,
            emoji=target_words.get(wc.word)
        )
        for wc in word_counts
    ]
    
    total_words = sum(wc.count for wc in word_counts)
    
    return UserSessionStatsResponse(
        session_id=session_id,
        user_id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        word_counts=word_count_list,
        total_words=total_words,
        session_started_at=session.started_at,
        session_duration=session.duration_seconds
    )


@router.get("/compare", response_model=SessionComparisonResponse)
async def compare_sessions(
    session_ids: List[uuid.UUID] = Query(..., description="List of session IDs to compare"),
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare my performance across multiple sessions.
    Shows how I did in different recording sessions.
    
    Args:
        session_ids: List of session IDs to compare (2-10 sessions)
        
    Returns:
        Comparison of stats across sessions
    """
    if len(session_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least 2 sessions to compare"
        )
    
    if len(session_ids) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare more than 10 sessions at once"
        )
    
    # Get target words for emoji mapping
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    # Build comparison data
    sessions_data = []
    total_across_all = 0
    
    for session_id in session_ids:
        # Get session
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        
        if not session:
            continue  # Skip missing sessions
        
        # Verify access
        member = db.query(GroupMember).filter(
            GroupMember.group_id == session.group_id,
            GroupMember.user_id == current_user.id
        ).first()
        
        if not member:
            continue  # Skip unauthorized sessions
        
        # Get word counts for this session
        word_counts = db.query(WordCount).filter(
            WordCount.session_id == session_id,
            WordCount.user_id == current_user.id
        ).all()
        
        word_count_list = [
            UserWordCountResponse(
                word=wc.word,
                count=wc.count,
                emoji=target_words.get(wc.word)
            )
            for wc in word_counts
        ]
        
        total_words = sum(wc.count for wc in word_counts)
        unique_words = len(set(wc.word for wc in word_counts))
        total_across_all += total_words
        
        sessions_data.append(SessionComparisonItem(
            session_id=session_id,
            started_at=session.started_at,
            total_words=total_words,
            unique_words=unique_words,
            word_counts=word_count_list
        ))
    
    # Sort by date
    sessions_data.sort(key=lambda x: x.started_at)
    
    # Calculate average
    average = total_across_all / len(sessions_data) if sessions_data else 0
    
    return SessionComparisonResponse(
        user_id=current_user.id,
        sessions=sessions_data,
        total_across_sessions=total_across_all,
        average_per_session=round(average, 1)
    )
