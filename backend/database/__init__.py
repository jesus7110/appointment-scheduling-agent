"""
Database module for PostgreSQL connection and SQLAlchemy models.
"""

from .connector import get_db, get_db_session, init_db
from .models import Appointment, ConversationHistory, SessionInfo
from .db_service import (
    store_or_update_session_info,
    store_conversation_history,
    finalize_session_on_disconnect,
    store_session_info_background,
    store_conversation_history_background,
    finalize_session_background,
    get_last_activity,
    set_last_activity,
    clear_last_activity,
)

__all__ = [
    "get_db",
    "get_db_session",
    "init_db",
    "Appointment",
    "ConversationHistory",
    "SessionInfo",
    "store_or_update_session_info",
    "store_conversation_history",
    "finalize_session_on_disconnect",
    "store_session_info_background",
    "store_conversation_history_background",
    "finalize_session_background",
    "get_last_activity",
    "set_last_activity",
    "clear_last_activity",
]

