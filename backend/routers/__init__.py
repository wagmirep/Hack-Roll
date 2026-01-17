"""
routers/__init__.py - Router Package Initialization

PURPOSE:
    Export all routers for easy importing in main.py
"""

from . import auth, groups, sessions, stats

__all__ = ["auth", "groups", "sessions", "stats"]
