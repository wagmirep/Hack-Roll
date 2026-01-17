"""
routers/stats.py - User Statistics Endpoints

PURPOSE:
    Define API endpoints for user statistics and Wrapped feature.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from auth import get_current_user
from models import WordCount, Profile, TargetWord, Session as SessionModel, GroupMember, Group
from schemas import MyStatsResponse, WordStatsResponse, WrappedResponse, GlobalLeaderboardResponse, UserStatsResponse, TrendDataPoint
import uuid
from typing import Optional, List
from datetime import datetime, timedelta

router = APIRouter(prefix="/users", tags=["Statistics"])


@router.get("/me/stats", response_model=MyStatsResponse)
async def get_my_stats(
    period: str = Query("all_time", regex="^(day|week|month|all_time)$"),
    group_id: Optional[uuid.UUID] = None,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's personal statistics.
    
    Args:
        period: Time period (day, week, month, all_time)
        group_id: Optional group filter
        
    Returns:
        User statistics
    """
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
    
    # Build query
    query = db.query(
        WordCount.word,
        func.sum(WordCount.count).label("total_count")
    ).filter(
        WordCount.user_id == current_user.id,
        WordCount.detected_at >= start_date
    )
    
    # Filter by group if specified
    if group_id:
        query = query.filter(WordCount.group_id == group_id)
    
    word_counts_query = query.group_by(WordCount.word).order_by(desc("total_count")).all()
    
    # Get target words with emojis
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    # Build word counts list
    word_counts = [
        WordStatsResponse(
            word=word,
            count=count,
            emoji=target_words.get(word)
        )
        for word, count in word_counts_query
    ]
    
    total_words = sum(wc.count for wc in word_counts)
    
    # Get favorite word (most used)
    favorite_word = word_counts[0].word if word_counts else None
    
    # Get total sessions
    session_query = db.query(SessionModel).join(
        WordCount, WordCount.session_id == SessionModel.id
    ).filter(
        WordCount.user_id == current_user.id,
        SessionModel.started_at >= start_date
    )
    
    if group_id:
        session_query = session_query.filter(SessionModel.group_id == group_id)
    
    total_sessions = session_query.distinct().count()
    
    # Get user's groups
    groups_query = db.query(Group).join(
        GroupMember, GroupMember.group_id == Group.id
    ).filter(
        GroupMember.user_id == current_user.id
    ).all()
    
    groups = [
        {
            "id": str(g.id),
            "name": g.name,
            "invite_code": g.invite_code
        }
        for g in groups_query
    ]
    
    return MyStatsResponse(
        user_id=current_user.id,
        period=period,
        total_words=total_words,
        total_sessions=total_sessions,
        word_counts=word_counts,
        favorite_word=favorite_word,
        groups=groups
    )


@router.get("/me/wrapped", response_model=WrappedResponse)
async def get_wrapped(
    year: Optional[int] = None,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Spotify Wrapped-style year recap.
    
    Args:
        year: Year to get wrapped for (defaults to current year)
        
    Returns:
        Wrapped statistics
    """
    # Default to current year
    if not year:
        year = datetime.utcnow().year
    
    # Calculate date range for the year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    
    # Get word counts for the year
    word_counts_query = db.query(
        WordCount.word,
        func.sum(WordCount.count).label("total_count")
    ).filter(
        WordCount.user_id == current_user.id,
        WordCount.detected_at >= start_date,
        WordCount.detected_at < end_date
    ).group_by(
        WordCount.word
    ).order_by(
        desc("total_count")
    ).limit(10).all()
    
    # Get target words with emojis
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    top_words = [
        WordStatsResponse(
            word=word,
            count=count,
            emoji=target_words.get(word)
        )
        for word, count in word_counts_query
    ]
    
    total_words = sum(wc.count for wc in top_words)
    
    # Get favorite word
    favorite_word = top_words[0].word if top_words else "lah"
    
    # Get total sessions
    total_sessions = db.query(SessionModel).join(
        WordCount, WordCount.session_id == SessionModel.id
    ).filter(
        WordCount.user_id == current_user.id,
        SessionModel.started_at >= start_date,
        SessionModel.started_at < end_date
    ).distinct().count()
    
    # Calculate percentile (compared to all users)
    all_user_totals = db.query(
        WordCount.user_id,
        func.sum(WordCount.count).label("total")
    ).filter(
        WordCount.detected_at >= start_date,
        WordCount.detected_at < end_date
    ).group_by(
        WordCount.user_id
    ).all()
    
    user_totals = sorted([total for _, total in all_user_totals], reverse=True)
    
    if total_words in user_totals:
        rank = user_totals.index(total_words) + 1
        percentile = int((1 - rank / len(user_totals)) * 100) if user_totals else 50
    else:
        percentile = 50
    
    # Generate fun facts
    fun_facts = []
    
    if total_words > 0:
        fun_facts.append(f"You said '{favorite_word}' {top_words[0].count} times this year!")
    
    if total_sessions > 0:
        avg_per_session = total_words / total_sessions
        fun_facts.append(f"You averaged {avg_per_session:.1f} Singlish words per session")
    
    if len(top_words) >= 3:
        fun_facts.append(f"Your top 3 words: {top_words[0].word}, {top_words[1].word}, {top_words[2].word}")
    
    if percentile >= 90:
        fun_facts.append("You're in the top 10% of Singlish speakers! 🎉")
    
    # Determine personality based on favorite word
    personality_map = {
        "lah": "The Classic Singaporean",
        "walao": "The Dramatic One",
        "siao": "The Wild Card",
        "shiok": "The Foodie",
        "paiseh": "The Polite One",
        "kan": "The Expressive One",
        "cheem": "The Intellectual",
        "lepak": "The Chill One",
        "steady": "The Reliable One",
        "bojio": "The FOMO Friend",
        "kiasu": "The Competitive One"
    }
    
    personality = personality_map.get(favorite_word, "The Singlish Speaker")
    
    # Determine badges
    badges = []
    if total_words >= 1000:
        badges.append("🏆 Word Master")
    if total_sessions >= 50:
        badges.append("🎤 Session King")
    if len(top_words) >= 8:
        badges.append("🌈 Vocabulary Expert")
    if percentile >= 90:
        badges.append("⭐ Top 10%")
    
    return WrappedResponse(
        user_id=current_user.id,
        year=year,
        total_words=total_words,
        total_sessions=total_sessions,
        top_words=top_words,
        favorite_word=favorite_word,
        percentile=percentile,
        fun_facts=fun_facts,
        personality=personality,
        badges=badges
    )


@router.get("/global/leaderboard", response_model=GlobalLeaderboardResponse)
async def get_global_leaderboard(
    period: str = Query("all_time", regex="^(day|week|month|all_time)$"),
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get global leaderboard across all users.
    
    Args:
        period: Time period (day, week, month, all_time)
        
    Returns:
        Global leaderboard statistics
    """
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
    
    # Get word counts by user
    user_word_counts = db.query(
        WordCount.user_id,
        WordCount.word,
        func.sum(WordCount.count).label("total_count")
    ).filter(
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
    
    # Get total unique users
    total_users = len(leaderboard)
    
    # Get total sessions in period
    total_sessions = db.query(SessionModel).filter(
        SessionModel.started_at >= start_date,
        SessionModel.status == "completed"
    ).count()
    
    # Get top words globally
    top_words_query = db.query(
        WordCount.word,
        func.sum(WordCount.count).label("total_count")
    ).filter(
        WordCount.detected_at >= start_date
    ).group_by(
        WordCount.word
    ).order_by(
        desc("total_count")
    ).limit(10).all()
    
    top_words = [
        WordStatsResponse(
            word=word,
            count=count,
            emoji=target_words.get(word)
        )
        for word, count in top_words_query
    ]
    
    return GlobalLeaderboardResponse(
        period=period,
        total_users=total_users,
        total_sessions=total_sessions,
        total_words=total_words,
        leaderboard=leaderboard,
        top_words=top_words
    )


@router.get("/me/trends", response_model=List[TrendDataPoint])
async def get_my_trends(
    granularity: str = Query("day", regex="^(day|week|month)$"),
    limit: int = Query(30, ge=1, le=365, description="Number of data points"),
    group_id: Optional[uuid.UUID] = None,
    current_user: Profile = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get usage trends over time.
    Shows how your Singlish usage has changed over time.
    
    Args:
        granularity: Data point interval (day, week, month)
        limit: Number of data points to return
        group_id: Optional group filter
        
    Returns:
        Time series of word counts
    """
    from sqlalchemy import case, cast, Date
    
    # Build date truncation based on granularity
    if granularity == "day":
        date_trunc = func.date_trunc('day', WordCount.detected_at)
    elif granularity == "week":
        date_trunc = func.date_trunc('week', WordCount.detected_at)
    else:  # month
        date_trunc = func.date_trunc('month', WordCount.detected_at)
    
    # Build query
    query = db.query(
        date_trunc.label('period'),
        func.sum(WordCount.count).label('total_words'),
        func.count(func.distinct(WordCount.session_id)).label('sessions')
    ).filter(
        WordCount.user_id == current_user.id
    )
    
    # Apply group filter
    if group_id:
        query = query.filter(WordCount.group_id == group_id)
    
    # Group and order
    trends = query.group_by('period').order_by(desc('period')).limit(limit).all()
    
    # Convert to response format
    result = [
        TrendDataPoint(
            period=trend.period,
            total_words=trend.total_words,
            sessions=trend.sessions
        )
        for trend in reversed(trends)  # Reverse to show chronological order
    ]
    
    return result
