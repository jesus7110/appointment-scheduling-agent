"""
SQLAlchemy models for database tables.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Date,
    Time,
    Text,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class AppointmentStatus(str, enum.Enum):
    """Appointment status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Appointment(Base):
    """
    Table to store appointments.
    
    Maps to the Appointment schema from models.schemas.
    """
    __tablename__ = "appointments"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    appointment_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Doctor information
    doctor_id = Column(String(100), nullable=False, index=True)
    doctor_name = Column(String(200), nullable=False)
    specialty = Column(String(100), nullable=False, index=True)
    
    # Clinic information
    clinic_id = Column(String(100), nullable=False, index=True)
    clinic_name = Column(String(200), nullable=False)
    clinic_address = Column(Text, nullable=False)
    
    # Patient information
    patient_name = Column(String(200), nullable=False)
    patient_phone = Column(String(50), nullable=False, index=True)
    patient_email = Column(String(200), nullable=False, index=True)
    patient_age = Column(Integer, nullable=True)
    patient_notes = Column(Text, nullable=True)
    
    # Appointment details
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=30)
    
    # Status and confirmation
    # Use String instead of Enum to match the database schema (VARCHAR with CHECK constraint)
    status = Column(
        String(20),
        nullable=False,
        default=AppointmentStatus.CONFIRMED.value,
        index=True
    )
    confirmation_code = Column(String(50), unique=True, nullable=False, index=True)
    
    # Financial
    consultation_fee = Column(Integer, nullable=False)
    
    # Additional notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_appointments_date_status', 'date', 'status'),
        Index('idx_appointments_doctor_date', 'doctor_id', 'date'),
        Index('idx_appointments_patient_email', 'patient_email'),
    )
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, appointment_id={self.appointment_id}, doctor={self.doctor_name}, date={self.date})>"


class ConversationHistory(Base):
    """
    Table to store conversation history.
    
    Stores messages from chat sessions with sessionId and clientId.
    """
    __tablename__ = "conversation_history"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Session and client identifiers
    session_id = Column(String(100), nullable=False, index=True)
    client_id = Column(String(100), nullable=False, index=True)
    
    # Message details
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # Metadata
    message_order = Column(Integer, nullable=False)  # Order within the session
    metadata_json = Column(Text, nullable=True)  # Additional metadata as JSON string
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_conversation_session_order', 'session_id', 'message_order'),
        Index('idx_conversation_client_created', 'client_id', 'created_at'),
        Index('idx_conversation_session_created', 'session_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, session_id={self.session_id}, role={self.role}, created_at={self.created_at})>"


class SessionInfo(Base):
    """
    Table to store high-level session information.

    Stores:
    - session_id, client_id
    - when session started / ended
    - optional metadata such as device, browser, IP, user agent, location
    - generic metadata JSON for anything extra
    """

    __tablename__ = "session_info"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Identifiers
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    client_id = Column(String(100), nullable=False, index=True)

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    ended_at = Column(DateTime, nullable=True, index=True)
    last_activity_at = Column(DateTime, nullable=True, index=True)

    # Optional metadata fields
    device = Column(String(200), nullable=True)
    browser = Column(String(200), nullable=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)

    # Generic metadata as JSON string
    metadata_json = Column(Text, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_session_info_client_started", "client_id", "started_at"),
        Index("idx_session_info_client_last_activity", "client_id", "last_activity_at"),
        Index("idx_session_info_started_ended", "started_at", "ended_at"),
    )

    def __repr__(self):
        return (
            f"<SessionInfo(id={self.id}, session_id={self.session_id}, "
            f"client_id={self.client_id}, started_at={self.started_at}, ended_at={self.ended_at})>"
        )

