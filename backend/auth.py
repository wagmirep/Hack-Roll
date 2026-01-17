"""
auth.py - JWT Authentication Middleware

PURPOSE:
    Validate Supabase JWT tokens and extract user information.
    Provides authentication dependency for protected endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from typing import Optional
from config import settings
from database import get_db
from models import Profile
import uuid

# Security scheme for Swagger UI
security = HTTPBearer()


def decode_jwt(token: str) -> dict:
    """
    Decode and validate Supabase JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode JWT using Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase doesn't use aud claim
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> uuid.UUID:
    """
    Extract user ID from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials from request
        
    Returns:
        User UUID from token
        
    Raises:
        HTTPException: If token is invalid or missing user ID
    """
    token = credentials.credentials
    payload = decode_jwt(token)
    
    # Extract user ID from token payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
        )
    
    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )


def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> Profile:
    """
    Get current user profile from database.
    
    Args:
        user_id: User UUID from JWT token
        db: Database session
        
    Returns:
        User profile object
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please complete signup.",
        )
    
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[Profile]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database session
        
    Returns:
        User profile or None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_jwt(token)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        user = db.query(Profile).filter(Profile.id == uuid.UUID(user_id)).first()
        return user
    except:
        return None
