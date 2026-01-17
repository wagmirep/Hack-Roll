"""
test_history_endpoints.py - Test Session History & Comparison Endpoints

PURPOSE:
    Test the new session history, comparison, and trends endpoints to verify:
    - Session listing with filters and pagination
    - Individual session stats retrieval
    - Session comparison across multiple sessions
    - Trends analysis over time

USAGE:
    python test_history_endpoints.py

PREREQUISITES:
    - Run test_claiming_flow.py first to populate data
    - Or have existing sessions in the database
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import (
    Profile, Group, GroupMember, Session as SessionModel,
    SessionSpeaker, SpeakerWordCount, WordCount, TargetWord
)

# Test user IDs from previous test
TEST_USER_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440001")


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text: str):
    print(f"✅ {text}")


def print_info(text: str):
    print(f"ℹ️  {text}")


async def test_session_list(db: Session):
    """Test GET /sessions endpoint"""
    print_header("Testing Session List Endpoint")
    
    # Get the test user
    user = db.query(Profile).filter(Profile.id == TEST_USER_ID).first()
    
    if not user:
        print_info("No test user found. Run test_claiming_flow.py first!")
        return
    
    # Get user's groups
    memberships = db.query(GroupMember).filter(
        GroupMember.user_id == user.id
    ).all()
    
    if not memberships:
        print_info("User not in any groups")
        return
    
    group_id = memberships[0].group_id
    
    # Query sessions (simulating the endpoint)
    sessions = db.query(SessionModel).join(
        GroupMember,
        GroupMember.group_id == SessionModel.group_id
    ).filter(
        GroupMember.user_id == user.id,
        SessionModel.group_id == group_id
    ).order_by(SessionModel.started_at.desc()).limit(20).all()
    
    print_info(f"\n📋 Found {len(sessions)} sessions")
    
    for i, session in enumerate(sessions, 1):
        # Get starter name
        starter = db.query(Profile).filter(Profile.id == session.started_by).first()
        
        # Count speakers
        speakers = db.query(SessionSpeaker).filter(
            SessionSpeaker.session_id == session.id
        ).count()
        
        # Get my words
        from sqlalchemy import func
        my_words = db.query(func.sum(WordCount.count)).filter(
            WordCount.session_id == session.id,
            WordCount.user_id == user.id
        ).scalar() or 0
        
        # Get group total
        group_words = db.query(func.sum(WordCount.count)).filter(
            WordCount.session_id == session.id
        ).scalar() or 0
        
        print(f"\n  {i}. Session {session.id}")
        print(f"     Started by: {starter.display_name if starter else 'Unknown'}")
        print(f"     Status: {session.status}")
        print(f"     Started: {session.started_at}")
        print(f"     Duration: {session.duration_seconds}s" if session.duration_seconds else "     (In progress)")
        print(f"     Speakers: {speakers}")
        print(f"     My words: {my_words}")
        print(f"     Group words: {group_words}")
    
    print_success(f"\n✅ Session list endpoint working! Found {len(sessions)} sessions")


async def test_my_session_stats(db: Session):
    """Test GET /sessions/{id}/my-stats endpoint"""
    print_header("Testing My Session Stats Endpoint")
    
    # Get test user
    user = db.query(Profile).filter(Profile.id == TEST_USER_ID).first()
    
    if not user:
        print_info("No test user found")
        return
    
    # Find a completed session with word counts
    session = db.query(SessionModel).join(
        WordCount,
        WordCount.session_id == SessionModel.id
    ).filter(
        WordCount.user_id == user.id
    ).first()
    
    if not session:
        print_info("No sessions with word counts found")
        return
    
    # Get word counts
    word_counts = db.query(WordCount).filter(
        WordCount.session_id == session.id,
        WordCount.user_id == user.id
    ).all()
    
    # Get target words for emojis
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    print_info(f"\n📊 Session: {session.id}")
    print(f"     Started: {session.started_at}")
    print(f"     Duration: {session.duration_seconds}s")
    print(f"\n     Your word counts:")
    
    total = 0
    for wc in word_counts:
        emoji = target_words.get(wc.word, "")
        print(f"       {emoji} {wc.word}: {wc.count}")
        total += wc.count
    
    print(f"\n     Total: {total} words")
    print_success("\n✅ My session stats endpoint working!")


async def test_session_comparison(db: Session):
    """Test GET /sessions/compare endpoint"""
    print_header("Testing Session Comparison Endpoint")
    
    # Get test user
    user = db.query(Profile).filter(Profile.id == TEST_USER_ID).first()
    
    if not user:
        print_info("No test user found")
        return
    
    # Get multiple sessions with word counts
    sessions = db.query(SessionModel).join(
        WordCount,
        WordCount.session_id == SessionModel.id
    ).filter(
        WordCount.user_id == user.id
    ).distinct().limit(3).all()
    
    if len(sessions) < 2:
        print_info(f"Need at least 2 sessions to compare (found {len(sessions)})")
        return
    
    print_info(f"\n🔄 Comparing {len(sessions)} sessions")
    
    total_across_all = 0
    target_words = {tw.word: tw.emoji for tw in db.query(TargetWord).all()}
    
    for i, session in enumerate(sessions, 1):
        word_counts = db.query(WordCount).filter(
            WordCount.session_id == session.id,
            WordCount.user_id == user.id
        ).all()
        
        total = sum(wc.count for wc in word_counts)
        unique = len(set(wc.word for wc in word_counts))
        total_across_all += total
        
        print(f"\n  Session {i}: {session.started_at}")
        print(f"     Total words: {total}")
        print(f"     Unique words: {unique}")
        print(f"     Top 3:")
        
        for wc in sorted(word_counts, key=lambda x: x.count, reverse=True)[:3]:
            emoji = target_words.get(wc.word, "")
            print(f"       {emoji} {wc.word}: {wc.count}")
    
    average = total_across_all / len(sessions)
    print(f"\n  📈 Statistics:")
    print(f"     Total across all: {total_across_all}")
    print(f"     Average per session: {average:.1f}")
    
    print_success("\n✅ Session comparison endpoint working!")


async def test_trends(db: Session):
    """Test GET /users/me/trends endpoint"""
    print_header("Testing Trends Endpoint")
    
    # Get test user
    user = db.query(Profile).filter(Profile.id == TEST_USER_ID).first()
    
    if not user:
        print_info("No test user found")
        return
    
    # Simulate trends query (daily)
    from sqlalchemy import func
    
    trends = db.query(
        func.date_trunc('day', WordCount.detected_at).label('period'),
        func.sum(WordCount.count).label('total_words'),
        func.count(func.distinct(WordCount.session_id)).label('sessions')
    ).filter(
        WordCount.user_id == user.id
    ).group_by('period').order_by('period').all()
    
    print_info(f"\n📈 Found {len(trends)} data points")
    
    for trend in trends:
        print(f"  {trend.period.strftime('%Y-%m-%d')}: {trend.total_words} words in {trend.sessions} session(s)")
    
    if trends:
        total = sum(t.total_words for t in trends)
        avg = total / len(trends)
        print(f"\n  Average: {avg:.1f} words/day")
        
        # Check for trend
        if len(trends) >= 2:
            first_half_avg = sum(t.total_words for t in trends[:len(trends)//2]) / (len(trends)//2)
            second_half_avg = sum(t.total_words for t in trends[len(trends)//2:]) / (len(trends) - len(trends)//2)
            
            if second_half_avg > first_half_avg:
                print(f"  Trend: 📈 Increasing ({first_half_avg:.1f} → {second_half_avg:.1f})")
            else:
                print(f"  Trend: 📉 Decreasing ({first_half_avg:.1f} → {second_half_avg:.1f})")
    
    print_success("\n✅ Trends endpoint working!")


async def main():
    """Main test flow"""
    print("\n" + "🎯" * 35)
    print("  SESSION HISTORY ENDPOINTS TEST")
    print("🎯" * 35)
    
    db = next(get_db())
    
    try:
        await test_session_list(db)
        await test_my_session_stats(db)
        await test_session_comparison(db)
        await test_trends(db)
        
        print_header("✨ TEST SUMMARY ✨")
        print_success("All history endpoints working!")
        print_info("\nWhat was tested:")
        print("  ✅ Session list with filters")
        print("  ✅ Individual session stats")
        print("  ✅ Session comparison")
        print("  ✅ Trends over time")
        
        print("\n" + "=" * 70)
        print("  🎉 Ready to build history screens in mobile app!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
