"""
routers/auth.py - Authentication Endpoints

PURPOSE:
    Define API endpoints for user authentication and profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from auth import get_current_user, get_current_user_id
from models import Profile, GroupMember, Group
from schemas import ProfileResponse, ProfileUpdateRequest, MeResponse, GroupResponse, UserSearchResponse, UserSearchResult
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information and their groups.
    
    Returns:
        User profile and list of groups they belong to
    """
    # Get user's groups
    group_memberships = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id
    ).all()
    
    groups = []
    for membership in group_memberships:
        group = db.query(Group).filter(Group.id == membership.group_id).first()
        if group:
            # Count members
            member_count = db.query(GroupMember).filter(
                GroupMember.group_id == group.id
            ).count()
            
            group_dict = {
                "id": group.id,
                "name": group.name,
                "created_by": group.created_by,
                "invite_code": group.invite_code,
                "created_at": group.created_at,
                "member_count": member_count
            }
            groups.append(group_dict)
    
    return {
        "profile": current_user,
        "groups": groups
    }


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    updates: ProfileUpdateRequest,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    Args:
        updates: Profile fields to update
        
    Returns:
        Updated user profile
    """
    # Update fields if provided
    if updates.display_name is not None:
        current_user.display_name = updates.display_name
    
    if updates.avatar_url is not None:
        current_user.avatar_url = updates.avatar_url
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_user_profile(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)  # Require auth
):
    """
    Get another user's profile by ID.
    
    Args:
        user_id: User ID to look up
        
    Returns:
        User profile
    """
    user = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/search", response_model=UserSearchResponse)
async def search_users(
    query: str = Query(..., min_length=1, max_length=100, description="Search query for username or display name"),
    group_id: uuid.UUID = Query(None, description="Optional: filter users by group membership"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Search for users by username or display name.
    Useful for tagging speakers in sessions.
    
    Args:
        query: Search string (matches username or display_name)
        group_id: Optional group ID to filter users who are in the same group
        limit: Maximum number of results to return
        
    Returns:
        List of matching users
    """
    # Build base query
    search_query = db.query(Profile).filter(
        or_(
            Profile.username.ilike(f"%{query}%"),
            Profile.display_name.ilike(f"%{query}%")
        )
    )
    
    # Filter by group if specified
    if group_id:
        # Verify current user is in this group
        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this group"
            )
        
        # Only return users who are members of the specified group
        search_query = search_query.join(GroupMember).filter(
            GroupMember.group_id == group_id
        )
    
    # Execute query with limit
    users = search_query.limit(limit).all()
    
    # Count total results
    total = search_query.count()
    
    # Convert to response format
    user_results = [
        UserSearchResult(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url
        )
        for user in users
    ]
    
    return UserSearchResponse(
        users=user_results,
        total=total
    )
