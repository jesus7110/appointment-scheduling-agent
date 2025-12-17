"""
Pydantic schemas for the appointment scheduling system.

These schemas provide:
- Data validation for JSON files
- Type safety throughout the application
- Automatic API documentation
- Request/response validation
"""
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================================================
# Category 1: Clinic Data Models
# ============================================================================

class Address(BaseModel):
    """Physical address of a clinic."""
    street: str
    area: str
    city: str
    state: str
    pincode: str
    country: str = "India"


class Contact(BaseModel):
    """Contact information."""
    phone: str
    email: EmailStr
    emergency: Optional[str] = None


class DayHours(BaseModel):
    """Operating hours for a single day."""
    open: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Opening time in HH:MM format")
    close: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Closing time in HH:MM format")


class OperatingHours(BaseModel):
    """Weekly operating schedule for a clinic."""
    monday: Union[DayHours, str]  # Can be DayHours or "closed"
    tuesday: Union[DayHours, str]
    wednesday: Union[DayHours, str]
    thursday: Union[DayHours, str]
    friday: Union[DayHours, str]
    saturday: Union[DayHours, str]
    sunday: Union[DayHours, str]


class Clinic(BaseModel):
    """Complete clinic information."""
    id: str
    name: str
    address: Address
    contact: Contact
    specialties: List[str]
    operating_hours: OperatingHours
    appointment_duration_minutes: int = 30
    timezone: str = "Asia/Kolkata"


class GeneralInfo(BaseModel):
    """General booking policies and information."""
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    language: str = "en"
    booking_advance_days: int = 30
    cancellation_hours: int = 24
    emergency_contact: str


# ============================================================================
# Category 2: Doctor Data Models
# ============================================================================

class TimeSlot(BaseModel):
    """A single time range (used for availability)."""
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Start time in HH:MM format")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="End time in HH:MM format")


class DoctorAvailability(BaseModel):
    """Weekly availability schedule for a doctor."""
    monday: Optional[List[TimeSlot]] = []
    tuesday: Optional[List[TimeSlot]] = []
    wednesday: Optional[List[TimeSlot]] = []
    thursday: Optional[List[TimeSlot]] = []
    friday: Optional[List[TimeSlot]] = []
    saturday: Optional[List[TimeSlot]] = []
    sunday: Optional[List[TimeSlot]] = []


class DoctorContact(BaseModel):
    """Doctor's contact information."""
    phone: str
    email: EmailStr


class Doctor(BaseModel):
    """Complete doctor information."""
    id: str
    name: str
    title: str
    specialty: str
    qualification: str
    experience_years: int
    consultation_fee: int  # in INR
    clinic_id: str
    clinic_name: str
    contact: DoctorContact
    languages: List[str]
    availability: DoctorAvailability
    blocked_dates: List[str] = []  # ISO date strings
    appointment_duration_minutes: int = 30


# ============================================================================
# Category 3: Appointment & Booking Models
# ============================================================================

class AppointmentStatus(str, Enum):
    """Status of an appointment."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PatientInfo(BaseModel):
    """Patient information for booking."""
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^\+?[\d\s\-\(\)]+$")
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)
    notes: Optional[str] = Field(None, max_length=500)


class AppointmentSlot(BaseModel):
    """An available appointment slot with doctor and clinic info."""
    doctor_id: str
    doctor_name: str
    specialty: str
    clinic_id: str
    clinic_name: str
    clinic_address: str  # Brief address for display
    date: date
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    duration_minutes: int
    consultation_fee: int


class Appointment(BaseModel):
    """A confirmed appointment."""
    appointment_id: str
    doctor_id: str
    doctor_name: str
    specialty: str
    clinic_id: str
    clinic_name: str
    clinic_address: str
    patient_info: PatientInfo
    date: date
    start_time: str
    end_time: str
    duration_minutes: int
    status: AppointmentStatus = AppointmentStatus.CONFIRMED
    confirmation_code: str
    created_at: datetime
    consultation_fee: int
    notes: Optional[str] = None


# ============================================================================
# Category 4: API Request/Response Models
# ============================================================================

class ChatMessage(BaseModel):
    """A single message in a conversation."""
    role: str = Field(..., pattern=r"^(user|assistant|system)$")
    content: str


class BotAction(BaseModel):
    """An action option for selection messages."""
    key: str
    value: Optional[str] = None


class BotMessageData(BaseModel):
    """Payload for bot message types."""
    msg_body: str
    action: Optional[List[BotAction]] = None


class BotMessage(BaseModel):
    """Structured bot message used by the frontend."""
    msg_type: str = Field(..., pattern=r"^(text|action1)$")
    data: BotMessageData
    # Optional UI flags (frontend controlled)
    actionsDisabled: Optional[bool] = None
    selectedAction: Optional[str] = None


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    messages: List[ChatMessage] = Field(..., min_length=1)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AppointmentSummary(BaseModel):
    """Summary of an appointment (for chat response)."""
    doctor_name: str
    specialty: str
    clinic_name: str
    date: str
    time: str
    confirmation_code: str
    consultation_fee: int


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    message: str  # Plain text reply (backward compatible)
    bot_message: Optional[BotMessage] = None  # Structured reply for UI
    appointment_summary: Optional[AppointmentSummary] = None
    suggested_actions: Optional[List[str]] = None
    session_id: Optional[str] = None


class AvailabilityRequest(BaseModel):
    """Request to check doctor availability."""
    specialty: Optional[str] = None
    doctor_id: Optional[str] = None
    clinic_id: Optional[str] = None
    date: Optional[date] = None
    date_start: Optional[date] = None
    date_end: Optional[date] = None


class AvailabilityResponse(BaseModel):
    """Response with available appointment slots."""
    slots: List[AppointmentSlot]
    total_count: int


class BookingRequest(BaseModel):
    """Request to book an appointment."""
    doctor_id: str
    clinic_id: str
    date: date
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    patient_info: PatientInfo


class BookingResponse(BaseModel):
    """Response after attempting to book an appointment."""
    success: bool
    appointment: Optional[Appointment] = None
    error_message: Optional[str] = None
    confirmation_code: Optional[str] = None


# ============================================================================
# Category 5: Tool Models (for LLM agent tools)
# ============================================================================

class AvailabilityToolInput(BaseModel):
    """Input parameters for the availability checking tool."""
    specialty: Optional[str] = Field(None, description="Medical specialty (e.g., Cardiology, Pediatrics)")
    doctor_name: Optional[str] = Field(None, description="Doctor's name or partial name")
    clinic_name: Optional[str] = Field(None, description="Clinic name or area")
    date: Optional[str] = Field(None, description="Preferred date in YYYY-MM-DD format")
    preferred_time: Optional[str] = Field(None, description="Preferred time of day (morning/afternoon/evening)")


class AvailabilityToolOutput(BaseModel):
    """Output from the availability checking tool."""
    available_slots: List[AppointmentSlot]
    message: str  # Human-readable summary
    total_count: int


class BookingToolInput(BaseModel):
    """Input parameters for the appointment booking tool."""
    doctor_id: str = Field(..., description="ID of the doctor to book with")
    date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    time: str = Field(..., description="Appointment time in HH:MM format")
    patient_name: str = Field(..., description="Patient's full name")
    patient_phone: str = Field(..., description="Patient's phone number")
    patient_email: str = Field(..., description="Patient's email address")
    patient_age: Optional[int] = Field(None, description="Patient's age")
    notes: Optional[str] = Field(None, description="Additional notes or reason for visit")


class BookingToolOutput(BaseModel):
    """Output from the appointment booking tool."""
    success: bool
    appointment: Optional[Appointment] = None
    message: str  # Human-readable result
    confirmation_code: Optional[str] = None
    error_message: Optional[str] = None


# ============================================================================
# Container Models for Data Loading
# ============================================================================

class ClinicData(BaseModel):
    """Container for all clinic data from clinic_info.json."""
    clinics: List[Clinic]
    general_info: GeneralInfo


class DoctorData(BaseModel):
    """Container for all doctor data from doctor_schedule.json."""
    doctors: List[Doctor]
