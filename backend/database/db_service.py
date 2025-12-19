"""
Async database service for managing session info and conversation history.

This module provides async functions to:
- Store/update session_info when WebSocket connects/disconnects
- Track last_activity_at per session (last user message timestamp)
- Store conversation history messages
- All operations are non-blocking to avoid affecting chat performance
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update
import logging

from .models import SessionInfo, ConversationHistory

logger = logging.getLogger(__name__)

# Convert sync DATABASE_URL to async (postgresql:// -> postgresql+asyncpg://)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/appointment_scheduling"
)

# Convert to async driver
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# In-memory storage for last_activity_at per session
# Format: {session_id: datetime}
_last_activity_tracker: Dict[str, datetime] = {}


def get_last_activity(session_id: str) -> Optional[datetime]:
    """Get the last activity timestamp for a session."""
    return _last_activity_tracker.get(session_id)


def set_last_activity(session_id: str, timestamp: datetime) -> None:
    """Set the last activity timestamp for a session."""
    _last_activity_tracker[session_id] = timestamp


def clear_last_activity(session_id: str) -> None:
    """Clear the last activity timestamp for a session."""
    _last_activity_tracker.pop(session_id, None)


async def store_or_update_session_info(
    session_id: str,
    client_id: str,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
    device: Optional[str] = None,
    browser: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    location: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> bool:
    """
    Store or update session_info in the database.
    
    This function:
    - Creates a new session_info record if it doesn't exist
    - Updates existing record if session_id already exists
    - Can be called on WebSocket connect (to store started_at)
    - Can be called on WebSocket disconnect (to update ended_at and last_activity_at)
    
    Args:
        session_id: Unique session identifier
        client_id: Client identifier
        started_at: When session started (defaults to now if not provided)
        ended_at: When session ended (None for active sessions)
        device: Optional device information
        browser: Optional browser information
        ip_address: Optional IP address
        user_agent: Optional user agent string
        location: Optional location information
        metadata: Optional dictionary of additional metadata (will be JSON encoded)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Check if session_info already exists
            result = await session.execute(
                select(SessionInfo).where(SessionInfo.session_id == session_id)
            )
            existing_session = result.scalar_one_or_none()
            
            if existing_session:
                # Update existing session
                update_data = {}
                if ended_at is not None:
                    update_data["ended_at"] = ended_at
                if started_at is not None:
                    update_data["started_at"] = started_at
                if device is not None:
                    update_data["device"] = device
                if browser is not None:
                    update_data["browser"] = browser
                if ip_address is not None:
                    update_data["ip_address"] = ip_address
                if user_agent is not None:
                    update_data["user_agent"] = user_agent
                if location is not None:
                    update_data["location"] = location
                if metadata is not None:
                    update_data["metadata_json"] = json.dumps(metadata)
                
                # Update last_activity_at from tracker if available
                last_activity = get_last_activity(session_id)
                if last_activity:
                    update_data["last_activity_at"] = last_activity
                
                if update_data:
                    await session.execute(
                        update(SessionInfo)
                        .where(SessionInfo.session_id == session_id)
                        .values(**update_data)
                    )
                    await session.commit()
                    logger.info(f"Updated session_info for session_id={session_id}")
            else:
                # Create new session
                if started_at is None:
                    started_at = datetime.utcnow()
                
                # Get last_activity_at from tracker if available
                last_activity = get_last_activity(session_id)
                
                new_session = SessionInfo(
                    session_id=session_id,
                    client_id=client_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    last_activity_at=last_activity,
                    device=device,
                    browser=browser,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    location=location,
                    metadata_json=json.dumps(metadata) if metadata else None,
                )
                session.add(new_session)
                await session.commit()
                logger.info(f"Created session_info for session_id={session_id}, client_id={client_id}")
            
            return True
            
    except Exception as e:
        logger.error(f"Error storing/updating session_info for session_id={session_id}: {e}", exc_info=True)
        return False


async def store_conversation_history(
    session_id: str,
    client_id: str,
    role: str,
    content: str,
    message_order: Optional[int] = None,
    metadata: Optional[dict] = None,
) -> bool:
    """
    Store a conversation history message in the database.
    
    This function is async and non-blocking, so it won't affect chat performance.
    
    Args:
        session_id: Session identifier
        client_id: Client identifier
        role: Message role ('user', 'assistant', 'system')
        content: Message content
        message_order: Optional message order (if None, will query for max + 1)
        metadata: Optional dictionary of additional metadata (will be JSON encoded)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # If message_order not provided, get the next order number
            if message_order is None:
                result = await session.execute(
                    select(ConversationHistory.message_order)
                    .where(ConversationHistory.session_id == session_id)
                    .order_by(ConversationHistory.message_order.desc())
                    .limit(1)
                )
                last_order = result.scalar_one_or_none()
                message_order = (last_order + 1) if last_order is not None else 1
            
            # Create new conversation history entry
            conversation = ConversationHistory(
                session_id=session_id,
                client_id=client_id,
                role=role,
                content=content,
                message_order=message_order,
                metadata_json=json.dumps(metadata) if metadata else None,
            )
            
            session.add(conversation)
            await session.commit()
            
            # If this is a user message, update last_activity tracker
            if role == "user":
                set_last_activity(session_id, datetime.utcnow())
            
            logger.debug(f"Stored conversation history: session_id={session_id}, role={role}, order={message_order}")
            return True
            
    except Exception as e:
        logger.error(f"Error storing conversation history for session_id={session_id}: {e}", exc_info=True)
        return False


async def finalize_session_on_disconnect(session_id: str) -> bool:
    """
    Finalize session when WebSocket disconnects.
    
    This function:
    1. Gets the last_activity_at from the in-memory tracker
    2. Updates session_info with ended_at and last_activity_at
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        last_activity = get_last_activity(session_id)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SessionInfo).where(SessionInfo.session_id == session_id)
            )
            existing_session = result.scalar_one_or_none()
            
            if existing_session:
                update_data = {
                    "ended_at": datetime.utcnow(),
                }
                
                if last_activity:
                    update_data["last_activity_at"] = last_activity
                
                await session.execute(
                    update(SessionInfo)
                    .where(SessionInfo.session_id == session_id)
                    .values(**update_data)
                )
                await session.commit()
                
                # Clear the tracker for this session
                clear_last_activity(session_id)
                
                logger.info(f"Finalized session_info for session_id={session_id}, ended_at={update_data['ended_at']}")
                return True
            else:
                logger.warning(f"Session_info not found for session_id={session_id} during disconnect")
                return False
                
    except Exception as e:
        logger.error(f"Error finalizing session for session_id={session_id}: {e}", exc_info=True)
        return False


# Background task helpers (fire-and-forget)
def store_conversation_history_background(
    session_id: str,
    client_id: str,
    role: str,
    content: str,
    message_order: Optional[int] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Fire-and-forget wrapper for store_conversation_history.
    Creates a background task that won't block the main flow.
    """
    asyncio.create_task(
        store_conversation_history(session_id, client_id, role, content, message_order, metadata)
    )


def store_session_info_background(
    session_id: str,
    client_id: str,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
    device: Optional[str] = None,
    browser: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    location: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Fire-and-forget wrapper for store_or_update_session_info.
    Creates a background task that won't block the main flow.
    """
    asyncio.create_task(
        store_or_update_session_info(
            session_id, client_id, started_at, ended_at,
            device, browser, ip_address, user_agent, location, metadata
        )
    )


def finalize_session_background(session_id: str) -> None:
    """
    Fire-and-forget wrapper for finalize_session_on_disconnect.
    Creates a background task that won't block the main flow.
    """
    asyncio.create_task(finalize_session_on_disconnect(session_id))

