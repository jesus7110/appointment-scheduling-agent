"""
Appointment Manager - Functions for booking and managing appointments.

This module provides:
- Appointment ID generation (APP-00001 format)
- Store appointments in database
- Fetch appointments by various criteria
- Validation and helper functions
"""

import asyncio
import logging
import re
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Appointment, AppointmentStatus
from database.db_service import AsyncSessionLocal
from utils.data_loader import get_doctor_by_id, get_clinic_by_id

logger = logging.getLogger(__name__)


async def generate_appointment_id() -> str:
    """
    Generate a unique appointment ID in format APP-00001.
    
    Format: APP-XXXXX where XXXXX is a zero-padded 5-digit number.
    
    Returns:
        Appointment ID string (e.g., "APP-00001")
    """
    try:
        # Get the highest existing appointment_id number
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Appointment.appointment_id)
                .where(Appointment.appointment_id.like("APP-%"))
                .order_by(Appointment.appointment_id.desc())
                .limit(1)
            )
            max_id = result.scalar_one_or_none()
        
        if max_id:
            # Extract number from "APP-00001" format
            try:
                number = int(max_id.split("-")[1])
                next_number = number + 1
            except (ValueError, IndexError):
                # If format is wrong, start from 1
                next_number = 1
        else:
            # No existing appointments, start from 1
            next_number = 1
        
        # Format as APP-00001 (5 digits, zero-padded)
        appointment_id = f"APP-{next_number:05d}"
        
        logger.info(f"✅ Generated appointment_id: {appointment_id} (next_number={next_number})")
        print(f"[APPOINTMENT_ID] Generated: {appointment_id}")
        return appointment_id
        
    except Exception as e:
        logger.error(f"Error generating appointment_id: {e}", exc_info=True)
        # Fallback: use timestamp-based ID
        timestamp = int(datetime.now().timestamp())
        return f"APP-{timestamp:05d}"


def get_required_booking_fields() -> List[str]:
    """
    Get list of required fields for booking an appointment.
    
    Returns:
        List of required field names
    """
    return [
        "doctor_id",
        "clinic_id",
        "patient_name",
        "patient_phone",
        "patient_email",
        "appointment_date",
        "appointment_time",
    ]


def validate_booking_data(booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all required fields are present for booking.
    
    Args:
        booking_data: Dictionary with booking information
        
    Returns:
        Dict with:
            - valid: bool
            - missing_fields: List[str] (if invalid)
            - errors: List[str] (if invalid)
    """
    required_fields = get_required_booking_fields()
    missing_fields = []
    errors = []
    
    # Check for missing required fields
    for field in required_fields:
        if field not in booking_data or booking_data[field] is None:
            missing_fields.append(field)
    
    # Validate date format if present
    if "appointment_date" in booking_data and booking_data["appointment_date"]:
        try:
            if isinstance(booking_data["appointment_date"], str):
                date.fromisoformat(booking_data["appointment_date"])
        except (ValueError, TypeError):
            errors.append("appointment_date must be in YYYY-MM-DD format")
    
    # Validate time format if present
    if "appointment_time" in booking_data and booking_data["appointment_time"]:
        try:
            if isinstance(booking_data["appointment_time"], str):
                time.fromisoformat(booking_data["appointment_time"])
        except (ValueError, TypeError):
            errors.append("appointment_time must be in HH:MM format")
    
    # Validate email format if present
    if "patient_email" in booking_data and booking_data["patient_email"]:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, booking_data["patient_email"]):
            errors.append("patient_email must be a valid email address")
    
    # Validate phone format if present
    if "patient_phone" in booking_data and booking_data["patient_phone"]:
        phone_pattern = r'^\+?[\d\s\-\(\)]+$'
        if not re.match(phone_pattern, booking_data["patient_phone"]):
            errors.append("patient_phone must be a valid phone number")
    
    if missing_fields or errors:
        return {
            "valid": False,
            "missing_fields": missing_fields,
            "errors": errors
        }
    
    return {
        "valid": True,
        "missing_fields": [],
        "errors": []
    }


async def generate_confirmation_code() -> str:
    """
    Generate a unique confirmation code for appointments.
    
    Format: 6-character alphanumeric code (e.g., "A1B2C3")
    
    Returns:
        Confirmation code string
    """
    import random
    import string
    
    # Generate 6-character code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Check if code already exists (unlikely but possible)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Appointment.confirmation_code)
            .where(Appointment.confirmation_code == code)
        )
        code_exists = result.scalar_one_or_none() is not None
    
    # If code exists, generate a new one (very unlikely)
    if code_exists:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    return code


async def create_appointment(
    doctor_id: str,
    clinic_id: str,
    patient_name: str,
    patient_phone: str,
    patient_email: str,
    appointment_date: date,
    appointment_time: time,
    patient_age: Optional[int] = None,
    patient_notes: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create and store an appointment in the database.
    
    This function:
    1. Validates doctor and clinic exist
    2. Calculates end_time based on duration
    3. Generates appointment_id and confirmation_code
    4. Stores appointment in database
    
    Args:
        doctor_id: ID of the doctor
        clinic_id: ID of the clinic
        patient_name: Patient's full name
        patient_phone: Patient's phone number
        patient_email: Patient's email address
        appointment_date: Date of appointment (YYYY-MM-DD)
        appointment_time: Start time of appointment (HH:MM)
        patient_age: Optional patient age
        patient_notes: Optional patient notes
        notes: Optional appointment notes
        
    Returns:
        Dict with:
            - success: bool
            - appointment_id: str (if successful)
            - confirmation_code: str (if successful)
            - appointment: Dict with appointment details (if successful)
            - error: str (if failed)
    """
    try:
        # Validate doctor exists
        doctor = get_doctor_by_id(doctor_id)
        if not doctor:
            return {
                "success": False,
                "error": f"Doctor with ID {doctor_id} not found"
            }
        
        # Validate clinic exists
        clinic = get_clinic_by_id(clinic_id)
        if not clinic:
            return {
                "success": False,
                "error": f"Clinic with ID {clinic_id} not found"
            }
        
        # Validate doctor is at this clinic
        if doctor.clinic_id != clinic_id:
            return {
                "success": False,
                "error": f"Doctor {doctor_id} is not associated with clinic {clinic_id}"
            }
        
        # Calculate end_time
        duration_minutes = doctor.appointment_duration_minutes
        start_datetime = datetime.combine(appointment_date, appointment_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_time = end_datetime.time()
        
        # Generate IDs
        logger.info(f"🔨 Starting appointment creation process...")
        appointment_id = await generate_appointment_id()
        confirmation_code = await generate_confirmation_code()
        logger.info(f"✅ Generated confirmation_code: {confirmation_code}")
        
        # Build clinic address string
        clinic_address = f"{clinic.address.street}, {clinic.address.area}, {clinic.address.city}, {clinic.address.state} {clinic.address.pincode}"
        
        # Prepare appointment data for logging
        appointment_data = {
            "appointment_id": appointment_id,
            "doctor_id": doctor_id,
            "doctor_name": doctor.name,
            "specialty": doctor.specialty,
            "clinic_id": clinic_id,
            "clinic_name": clinic.name,
            "clinic_address": clinic_address,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "patient_email": patient_email,
            "patient_age": patient_age,
            "patient_notes": patient_notes,
            "date": str(appointment_date),
            "start_time": str(appointment_time),
            "end_time": str(end_time),
            "duration_minutes": duration_minutes,
            "status": "confirmed",
            "confirmation_code": confirmation_code,
            "consultation_fee": doctor.consultation_fee,
            "notes": notes,
        }
        
        logger.info(f"📝 Appointment data to be stored: {appointment_data}")
        print(f"[APPOINTMENT_DATA] Attempting to store: {appointment_data}")
        
        # Create appointment record
        async with AsyncSessionLocal() as session:
            try:
                logger.info(f"🔧 Creating Appointment object for {appointment_id}")
                appointment = Appointment(
                    appointment_id=appointment_id,
                    doctor_id=doctor_id,
                    doctor_name=doctor.name,
                    specialty=doctor.specialty,
                    clinic_id=clinic_id,
                    clinic_name=clinic.name,
                    clinic_address=clinic_address,
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    patient_email=patient_email,
                    patient_age=patient_age,
                    patient_notes=patient_notes,
                    date=appointment_date,
                    start_time=appointment_time,
                    end_time=end_time,
                    duration_minutes=duration_minutes,
                    status=AppointmentStatus.CONFIRMED.value,
                    confirmation_code=confirmation_code,
                    consultation_fee=doctor.consultation_fee,
                    notes=notes,
                )
                
                logger.info(f"➕ Adding appointment to session: {appointment_id}")
                print(f"[DB_OPERATION] Adding appointment {appointment_id} to session")
                session.add(appointment)
                
                logger.info(f"💾 Committing appointment to database: {appointment_id}")
                print(f"[DB_OPERATION] Committing appointment {appointment_id} to database")
                await session.commit()
                
                logger.info(f"🔄 Refreshing appointment: {appointment_id}")
                await session.refresh(appointment)
                
                logger.info(f"✅ Successfully created appointment: {appointment_id} for doctor {doctor_id} on {appointment_date}")
                print(f"[SUCCESS] Appointment {appointment_id} successfully stored in database!")
            except Exception as db_error:
                logger.error(f"Database error while creating appointment {appointment_id}: {db_error}", exc_info=True)
                await session.rollback()
                raise  # Re-raise to be caught by outer exception handler
            
            # Return appointment details
            return {
                "success": True,
                "appointment_id": appointment_id,
                "confirmation_code": confirmation_code,
                "appointment": {
                    "appointment_id": appointment_id,
                    "doctor_name": doctor.name,
                    "doctor_id": doctor_id,
                    "specialty": doctor.specialty,
                    "clinic_name": clinic.name,
                    "clinic_id": clinic_id,
                    "clinic_address": clinic_address,
                    "patient_name": patient_name,
                    "patient_phone": patient_phone,
                    "patient_email": patient_email,
                    "date": appointment_date.isoformat(),
                    "start_time": appointment_time.strftime("%H:%M"),
                    "end_time": end_time.strftime("%H:%M"),
                    "duration_minutes": duration_minutes,
                    "consultation_fee": doctor.consultation_fee,
                    "confirmation_code": confirmation_code,
                    "status": "confirmed",
                }
            }
            
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error creating appointment: {error_type}: {error_msg}", exc_info=True)
        logger.error(f"Full traceback:", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to create appointment: {error_type}: {error_msg}",
            "error_type": error_type
        }


async def get_appointment_by_id(appointment_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch appointment details by appointment_id.
    
    Args:
        appointment_id: The appointment ID (e.g., "APP-00001")
        
    Returns:
        Dict with appointment details if found, None otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Appointment).where(Appointment.appointment_id == appointment_id)
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                return None
            
            return _appointment_to_dict(appointment)
            
    except Exception as e:
        logger.error(f"Error fetching appointment by ID {appointment_id}: {e}", exc_info=True)
        return None


async def get_appointments_by_patient_name(
    patient_name: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch appointments by patient name (partial match, case-insensitive).
    
    Args:
        patient_name: Patient name to search for
        limit: Maximum number of results to return
        
    Returns:
        List of appointment dicts matching the patient name
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Appointment)
                .where(Appointment.patient_name.ilike(f"%{patient_name}%"))
                .order_by(Appointment.date.desc(), Appointment.start_time.desc())
                .limit(limit)
            )
            appointments = result.scalars().all()
            
            return [_appointment_to_dict(apt) for apt in appointments]
            
    except Exception as e:
        logger.error(f"Error fetching appointments by patient name {patient_name}: {e}", exc_info=True)
        return []


async def get_appointments_by_date(
    appointment_date: date,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch all appointments for a specific date.
    
    Args:
        appointment_date: Date to search for
        status: Optional status filter (e.g., "confirmed", "cancelled")
        
    Returns:
        List of appointment dicts for that date
    """
    try:
        async with AsyncSessionLocal() as session:
            query = select(Appointment).where(Appointment.date == appointment_date)
            
            if status:
                query = query.where(Appointment.status == status)
            
            query = query.order_by(Appointment.start_time)
            
            result = await session.execute(query)
            appointments = result.scalars().all()
            
            return [_appointment_to_dict(apt) for apt in appointments]
            
    except Exception as e:
        logger.error(f"Error fetching appointments by date {appointment_date}: {e}", exc_info=True)
        return []


async def get_appointments_by_patient_phone(
    patient_phone: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch appointments by patient phone number.
    
    Args:
        patient_phone: Patient phone number
        limit: Maximum number of results to return
        
    Returns:
        List of appointment dicts for that phone number
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Appointment)
                .where(Appointment.patient_phone == patient_phone)
                .order_by(Appointment.date.desc(), Appointment.start_time.desc())
                .limit(limit)
            )
            appointments = result.scalars().all()
            
            return [_appointment_to_dict(apt) for apt in appointments]
            
    except Exception as e:
        logger.error(f"Error fetching appointments by phone {patient_phone}: {e}", exc_info=True)
        return []


async def get_appointments_by_doctor(
    doctor_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch appointments for a specific doctor.
    
    Args:
        doctor_id: Doctor ID
        start_date: Optional start date filter
        end_date: Optional end date filter
        status: Optional status filter
        
    Returns:
        List of appointment dicts for that doctor
    """
    try:
        async with AsyncSessionLocal() as session:
            query = select(Appointment).where(Appointment.doctor_id == doctor_id)
            
            if start_date:
                query = query.where(Appointment.date >= start_date)
            
            if end_date:
                query = query.where(Appointment.date <= end_date)
            
            if status:
                query = query.where(Appointment.status == status)
            
            query = query.order_by(Appointment.date, Appointment.start_time)
            
            result = await session.execute(query)
            appointments = result.scalars().all()
            
            return [_appointment_to_dict(apt) for apt in appointments]
            
    except Exception as e:
        logger.error(f"Error fetching appointments for doctor {doctor_id}: {e}", exc_info=True)
        return []


async def check_appointment_conflict(
    doctor_id: str,
    appointment_date: date,
    appointment_time: time,
    duration_minutes: int = 30
) -> bool:
    """
    Check if an appointment time conflicts with existing appointments.
    
    Args:
        doctor_id: Doctor ID
        appointment_date: Date to check
        appointment_time: Start time to check
        duration_minutes: Duration of the appointment
        
    Returns:
        True if there's a conflict, False if time slot is available
    """
    try:
        # Calculate end time
        start_datetime = datetime.combine(appointment_date, appointment_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        end_time = end_datetime.time()
        
        async with AsyncSessionLocal() as session:
            # Check for overlapping appointments
            # An appointment conflicts if:
            # - Same doctor, same date
            # - Status is confirmed (not cancelled)
            # - Time ranges overlap
            result = await session.execute(
                select(Appointment)
                .where(
                    and_(
                        Appointment.doctor_id == doctor_id,
                        Appointment.date == appointment_date,
                        Appointment.status == AppointmentStatus.CONFIRMED.value,
                        or_(
                            # New appointment starts during existing appointment
                            and_(
                                Appointment.start_time <= appointment_time,
                                Appointment.end_time > appointment_time
                            ),
                            # New appointment ends during existing appointment
                            and_(
                                Appointment.start_time < end_time,
                                Appointment.end_time >= end_time
                            ),
                            # New appointment completely contains existing appointment
                            and_(
                                Appointment.start_time >= appointment_time,
                                Appointment.end_time <= end_time
                            )
                        )
                    )
                )
            )
            
            conflicting = result.scalar_one_or_none()
            return conflicting is not None
            
    except Exception as e:
        logger.error(f"Error checking appointment conflict: {e}", exc_info=True)
        # On error, assume conflict exists (safer)
        return True


def _appointment_to_dict(appointment: Appointment) -> Dict[str, Any]:
    """
    Convert Appointment SQLAlchemy model to dictionary.
    
    Args:
        appointment: Appointment model instance
        
    Returns:
        Dictionary with appointment details
    """
    return {
        "appointment_id": appointment.appointment_id,
        "doctor_id": appointment.doctor_id,
        "doctor_name": appointment.doctor_name,
        "specialty": appointment.specialty,
        "clinic_id": appointment.clinic_id,
        "clinic_name": appointment.clinic_name,
        "clinic_address": appointment.clinic_address,
        "patient_name": appointment.patient_name,
        "patient_phone": appointment.patient_phone,
        "patient_email": appointment.patient_email,
        "patient_age": appointment.patient_age,
        "patient_notes": appointment.patient_notes,
        "date": appointment.date.isoformat() if appointment.date else None,
        "start_time": appointment.start_time.strftime("%H:%M") if appointment.start_time else None,
        "end_time": appointment.end_time.strftime("%H:%M") if appointment.end_time else None,
        "duration_minutes": appointment.duration_minutes,
        "status": appointment.status.value if hasattr(appointment.status, 'value') else str(appointment.status),
        "confirmation_code": appointment.confirmation_code,
        "consultation_fee": appointment.consultation_fee,
        "notes": appointment.notes,
        "created_at": appointment.created_at.isoformat() if appointment.created_at else None,
        "updated_at": appointment.updated_at.isoformat() if appointment.updated_at else None,
        "cancelled_at": appointment.cancelled_at.isoformat() if appointment.cancelled_at else None,
    }


async def cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel an appointment.
    
    Args:
        appointment_id: Appointment ID to cancel
        reason: Optional cancellation reason
        
    Returns:
        Dict with success status and message
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Appointment).where(Appointment.appointment_id == appointment_id)
            )
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                return {
                    "success": False,
                    "error": f"Appointment {appointment_id} not found"
                }
            
            if appointment.status == AppointmentStatus.CANCELLED.value:
                return {
                    "success": False,
                    "error": f"Appointment {appointment_id} is already cancelled"
                }
            
            # Update appointment status
            appointment.status = AppointmentStatus.CANCELLED.value
            appointment.cancelled_at = datetime.utcnow()
            if reason:
                appointment.notes = f"{appointment.notes or ''}\nCancellation reason: {reason}".strip()
            
            await session.commit()
            
            logger.info(f"Cancelled appointment: {appointment_id}")
            
            return {
                "success": True,
                "message": f"Appointment {appointment_id} has been cancelled",
                "appointment": _appointment_to_dict(appointment)
            }
            
    except Exception as e:
        logger.error(f"Error cancelling appointment {appointment_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to cancel appointment: {str(e)}"
        }

