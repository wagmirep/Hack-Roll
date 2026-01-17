"""
routers/groups.py - Group Management and Statistics Endpoints

PURPOSE:
    Define API endpoints for group management and statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from auth import get_current_user
from models import Group, GroupMember, Profile, WordCount, Session as SessionModel, TargetWord
from schemas import (
    GroupCreateRequest, GroupResponse, GroupJoinRequest,
    GroupMemberResponse, GroupStatsResponse, UserStatsResponse, WordStatsResponse
)
import uuid
import random
import string
from typing import List
from datetime import datetime, timedelta

router = APIRouter(prefix="/groups", tags=["Groups"])


def generate_invite_code(length: int = 8) -> str:
    """Generate random invite code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: GroupCreateRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new group.
    
    Args:
        request: Group creation details
        
    Returns:
        Created group with invite code
    """
    # Generate unique invite code
    invite_code = generate_invite_code()
    while db.query(Group).filter(Group.invite_code == invite_code).first():
        invite_code = generate_invite_code()
    
    # Create group
    group = Group(
        name=request.name,
        created_by=current_user.id,
        invite_code=invite_code
    )
    db.add(group)
    db.flush()
    
    # Add creator as admin member
    member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role="admin"
    )
    db.add(member)
    db.commit()
    db.refresh(group)
    
    # Add member count
    response = GroupResponse.model_validate(group)
    response.member_count = 1
    
    return response


@router.post("/join", response_model=GroupResponse)
async def join_group(
    request: GroupJoinRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join a group using invite code.
    
    Args:
        request: Invite code
        
    Returns:
        Joined group details
    """
    # Find group by invite code
    group = db.query(Group).filter(Group.invite_code == request.invite_code).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite code"
        )
    
    # Check if already a member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group.id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this group"
        )
    
    # Add as member
    member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role="member"
    )
    db.add(member)
    db.commit()
    
    # Get member count
    member_count = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()
    
    response = GroupResponse.model_validate(group)
    response.member_count = member_count
    
    return response


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_details(
    group_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get group details.
    
    Args:
        group_id: Group ID
        
    Returns:
        Group details
    """
    # Check membership
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this group"
        )
    
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get member count
    member_count = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
    
    response = GroupResponse.model_validate(group)
    response.member_count = member_count
    
    return response


@router.get("/{group_id}/members", response_model=List[GroupMemberResponse])
async def get_group_members(
    group_id: uuid.UUID,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all members of a group.
    
    Args:
        group_id: Group ID
        
    Returns:
        List of group members
    """
    # Check membership
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this group"
        )
    
    # Get all members with profile info
    members = db.query(GroupMember, Profile).join(
        Profile, GroupMember.user_id == Profile.id
    ).filter(
        GroupMember.group_id == group_id
    ).all()
    
    result = []
    for gm, profile in members:
        result.append(GroupMemberResponse(
            id=profile.id,
            username=profile.username,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            role=gm.role,
            joined_at=gm.joined_at
        ))
    
    return result


@router.get("/{group_id}/stats", response_model=GroupStatsResponse)
async def get_group_stats(
    group_id: uuid.UUID,
    period: str = Query("week", regex="^(day|week|month|all_time)$"),
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get group statistics and leaderboard.
    
    Args:
        group_id: Group ID
        period: Time period (day, week, month, all_time)
        
    Returns:
        Group statistics with leaderboard
    """
    # Check membership
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this group"
        )
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "day":
        start_date = now - timedelta(days=1)
    elif period == "week":
        start_date = now - timedelta(weeks=1)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # all_time
        start_date = datetime(2000, 1, 1)
    
    # Get group info
    group = db.query(Group).filter(Group.id == group_id).first()
    
    # Get total sessions in period
    total_sessions = db.query(SessionModel).filter(
        SessionModel.group_id == group_id,
        SessionModel.started_at >= start_date,
        SessionModel.status == "completed"
    ).count()
    
    # Get word counts by user
    user_word_counts = db.query(
        WordCount.user_id,
        WordCount.word,
        func.sum(WordCount.count).label("total_count")
    ).filter(
        WordCount.group_id == group_id,
        WordCount.detected_at >= start_date
    ).group_by(
        WordCount.user_id,
        WordCount.word
    ).all()
    
    # Get target words with emojis
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    # Organize by user
    user_stats_dict = {}
    total_words = 0
    
    for user_id, word, count in user_word_counts:
        if user_id not in user_stats_dict:
            user_stats_dict[user_id] = {
                "user_id": user_id,
                "word_counts": {},
                "total_words": 0
            }
        
        user_stats_dict[user_id]["word_counts"][word] = count
        user_stats_dict[user_id]["total_words"] += count
        total_words += count
    
    # Get user profiles and build leaderboard
    leaderboard = []
    for user_id, stats in user_stats_dict.items():
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if profile:
            word_counts = [
                WordStatsResponse(
                    word=word,
                    count=count,
                    emoji=target_words.get(word)
                )
                for word, count in stats["word_counts"].items()
            ]
            
            # Create top_words dictionary for frontend compatibility
            top_words = {word: count for word, count in stats["word_counts"].items()}
            
            leaderboard.append(UserStatsResponse(
                user_id=profile.id,
                username=profile.username,
                display_name=profile.display_name,
                avatar_url=profile.avatar_url,
                word_counts=word_counts,
                total_words=stats["total_words"],
                top_words=top_words
            ))
    
    # Sort by total words
    leaderboard.sort(key=lambda x: x.total_words, reverse=True)
    
    # Add ranks
    for i, user_stat in enumerate(leaderboard):
        user_stat.rank = i + 1
    
    # Get word breakdown (all words across all users)
    word_breakdown_query = db.query(
        WordCount.word,
        func.sum(WordCount.count).label("total_count")
    ).filter(
        WordCount.group_id == group_id,
        WordCount.detected_at >= start_date
    ).group_by(
        WordCount.word
    ).order_by(
        desc("total_count")
    ).all()
    
    word_breakdown = [
        WordStatsResponse(
            word=word,
            count=count,
            emoji=target_words.get(word)
        )
        for word, count in word_breakdown_query
    ]
    
    return GroupStatsResponse(
        group_id=group_id,
        group_name=group.name,
        period=period,
        total_sessions=total_sessions,
        total_words=total_words,
        leaderboard=leaderboard,
        word_breakdown=word_breakdown
    )
