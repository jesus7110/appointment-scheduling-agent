"""
Session management for client and conversation tracking.

- ClientId: Persistent identifier for a browser/device
- SessionId: Temporary identifier for a single conversation
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages client IDs and session IDs for conversations."""
    
    def __init__(self):
        # Store client information
        self.clients: Dict[str, dict] = {}
        
        # Store session (conversation) data
        self.sessions: Dict[str, dict] = {}
        
        # Track active WebSocket connections
        self.active_connections: Dict[str, 'WebSocket'] = {}
    
    def generate_client_id(self) -> str:
        """Generate a new unique client ID."""
        return f"client_{uuid.uuid4().hex[:16]}"
    
    def generate_session_id(self) -> str:
        """Generate a new unique session ID."""
        return f"session_{uuid.uuid4().hex[:16]}"
    
    def register_client(self, client_id: Optional[str] = None) -> str:
        """
        Register a client. If client_id provided, reuse it, otherwise create new.
        
        Args:
            client_id: Optional existing client ID
            
        Returns:
            Client ID (existing or newly created)
        """
        if client_id and client_id in self.clients:
            # Update last seen
            self.clients[client_id]["last_seen"] = datetime.now()
            logger.info(f"Client {client_id} reconnected")
            return client_id
        
        # Create new client
        if not client_id:
            client_id = self.generate_client_id()
        
        self.clients[client_id] = {
            "created_at": datetime.now(),
            "last_seen": datetime.now(),
            "session_count": 0
        }
        
        logger.info(f"New client registered: {client_id}")
        return client_id
    
    def create_session(self, client_id: str) -> str:
        """
        Create a new session for a client.
        
        Args:
            client_id: The client creating the session
            
        Returns:
            New session ID
        """
        if client_id not in self.clients:
            raise ValueError(f"Unknown client: {client_id}")
        
        session_id = self.generate_session_id()
        
        self.sessions[session_id] = {
            "client_id": client_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "messages": [],
            "metadata": {}
        }
        
        self.clients[client_id]["session_count"] += 1
        
        logger.info(f"New session created: {session_id} for client {client_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data by session ID."""
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Add a message to a session's history.
        
        Args:
            session_id: The session to add to
            role: Message role (user/assistant)
            content: Message content
            
        Returns:
            True if successful, False if session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Attempted to add message to unknown session: {session_id}")
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        session["messages"].append(message)
        session["last_activity"] = datetime.now()
        
        return True
    
    def get_messages(self, session_id: str) -> List[dict]:
        """Get all messages from a session."""
        session = self.sessions.get(session_id)
        if not session:
            return []
        return session["messages"]
    
    def register_connection(self, session_id: str, websocket) -> None:
        """Register an active WebSocket connection."""
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket registered for session {session_id}")
    
    def unregister_connection(self, session_id: str) -> None:
        """Unregister a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket unregistered for session {session_id}")
    
    def get_connection(self, session_id: str):
        """Get the active WebSocket connection for a session."""
        return self.active_connections.get(session_id)
    
    def cleanup_expired_sessions(self, max_age_minutes: int = 30) -> int:
        """
        Clean up sessions that haven't been active for max_age_minutes.
        
        Args:
            max_age_minutes: Maximum age in minutes before cleanup
            
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=max_age_minutes)
        
        expired_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if session["last_activity"] < cutoff
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            self.unregister_connection(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_stats(self) -> dict:
        """Get statistics about clients and sessions."""
        return {
            "total_clients": len(self.clients),
            "total_sessions": len(self.sessions),
            "active_connections": len(self.active_connections)
        }


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return _session_manager

