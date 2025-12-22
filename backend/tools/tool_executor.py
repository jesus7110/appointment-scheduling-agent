"""
Tool execution logic - maps tool calls to actual functions.
"""

import json
import logging
from typing import Dict, Any, Optional, List

from utils.data_loader import (
    search_doctors,
    search_clinics,
    get_doctor_by_id,
    get_clinic_by_id,
    get_clinic_with_doctors,
)
from utils.appointment_manager import (
    create_appointment,
    get_appointment_by_id,
    get_appointments_by_patient_name,
    get_appointments_by_date,
    get_appointments_by_patient_phone,
    validate_booking_data,
    cancel_appointment as cancel_appointment_func,
)
from datetime import date, time

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tool calls from the LLM."""
    
    def __init__(self):
        self.tool_map = {
            "end_conversation": self._end_conversation,
            "search_doctors": self._search_doctors,
            "search_clinics": self._search_clinics,
            "get_doctor_details": self._get_doctor_details,
            "get_clinic_details": self._get_clinic_details,
            "check_booking_readiness": self._check_booking_readiness,
            "book_appointment": self._book_appointment,
            "get_appointment": self._get_appointment,
            "find_appointments": self._find_appointments,
            "cancel_appointment": self._cancel_appointment,
        }
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.
        
        Handles both sync and async tools automatically.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool
            
        Returns:
            Dictionary with tool execution results and any special actions
        """
        if tool_name not in self.tool_map:
            error_msg = f"Unknown tool: {tool_name}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        try:
            tool_func = self.tool_map[tool_name]
            
            # Check if tool is async
            import asyncio
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)
            
            return result
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            logger.error(f"{error_msg} for tool {tool_name} with args {arguments}", exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _end_conversation(self, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        End the conversation and signal to close connection.
        
        Args:
            reason: Optional reason for ending
            
        Returns:
            Dict with success flag and close_connection signal
        """
        logger.info(f"End conversation requested. Reason: {reason or 'None provided'}")
        
        return {
            "success": True,
            "action": "close_connection",
            "message": "Goodbye! Thank you for using our appointment scheduling service. Have a great day! 👋",
            "reason": reason
        }
    
    def _search_doctors(
        self,
        name: Optional[str] = None,
        specialty: Optional[str] = None,
        max_fee: Optional[int] = None,
        language: Optional[str] = None,
        clinic_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for doctors with filters.
        
        Args:
            name: Doctor name to search for (partial match)
            specialty: Medical specialty to filter by
            max_fee: Maximum consultation fee in ₹
            language: Preferred language
            clinic_id: Filter by specific clinic
            
        Returns:
            Dict with count and list of matching doctors
        """
        try:
            doctors = search_doctors(
                name=name,
                specialty=specialty,
                max_fee=max_fee,
                language=language,
                clinic_id=clinic_id,
            )
            
            # Convert to dict format
            results = []
            for doctor in doctors:
                # Get availability days - DoctorAvailability is a Pydantic model
                availability_days = []
                if hasattr(doctor, 'availability') and doctor.availability:
                    # Check each day field in DoctorAvailability
                    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                    for day in days:
                        day_availability = getattr(doctor.availability, day, None)
                        if day_availability and len(day_availability) > 0:
                            availability_days.append(day)
                
                results.append({
                    "id": doctor.id,
                    "name": doctor.name,
                    "title": doctor.title,
                    "specialty": doctor.specialty,
                    "qualification": doctor.qualification,
                    "experience_years": doctor.experience_years,
                    "consultation_fee": doctor.consultation_fee,
                    "clinic_id": doctor.clinic_id,
                    "clinic_name": doctor.clinic_name,
                    "languages": doctor.languages,
                    "availability_days": availability_days,
                })
            
            logger.info(f"Search doctors: found {len(results)} doctors with filters name={name}, specialty={specialty}, max_fee={max_fee}, language={language}, clinic_id={clinic_id}")
            
            return {
                "success": True,
                "count": len(results),
                "doctors": results
            }
        except Exception as e:
            logger.error(f"Error searching doctors: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "doctors": []
            }
    
    def _search_clinics(
        self,
        city: Optional[str] = None,
        area: Optional[str] = None,
        specialty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search for clinics with filters.
        
        Args:
            city: City name to filter by
            area: Area/locality to filter by
            specialty: Medical specialty offered
            
        Returns:
            Dict with count and list of matching clinics
        """
        try:
            clinics = search_clinics(
                city=city,
                area=area,
                specialty=specialty,
            )
            
            # Convert to dict format
            results = []
            for clinic in clinics:
                results.append({
                    "id": clinic.id,
                    "name": clinic.name,
                    "address": {
                        "street": clinic.address.street,
                        "area": clinic.address.area,
                        "city": clinic.address.city,
                        "state": clinic.address.state,
                        "pincode": clinic.address.pincode,
                    },
                    "contact": {
                        "phone": clinic.contact.phone,
                        "email": clinic.contact.email,
                        "emergency": clinic.contact.emergency,
                    },
                    "specialties": clinic.specialties,
                    "operating_hours": clinic.operating_hours.dict() if hasattr(clinic.operating_hours, 'dict') else str(clinic.operating_hours),
                })
            
            logger.info(f"Search clinics: found {len(results)} clinics with filters city={city}, area={area}, specialty={specialty}")
            
            return {
                "success": True,
                "count": len(results),
                "clinics": results
            }
        except Exception as e:
            logger.error(f"Error searching clinics: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "clinics": []
            }
    
    def _get_doctor_details(self, doctor_id: str) -> Dict[str, Any]:
        """
        Get specific doctor details.
        
        Args:
            doctor_id: The doctor ID
            
        Returns:
            Dict with complete doctor information
        """
        try:
            doctor = get_doctor_by_id(doctor_id)
            
            if not doctor:
                return {
                    "success": False,
                    "error": f"Doctor with ID {doctor_id} not found"
                }
            
            # Convert to dict format
            result = {
                "success": True,
                "id": doctor.id,
                "name": doctor.name,
                "title": doctor.title,
                "specialty": doctor.specialty,
                "qualification": doctor.qualification,
                "experience_years": doctor.experience_years,
                "consultation_fee": doctor.consultation_fee,
                "clinic_id": doctor.clinic_id,
                "clinic_name": doctor.clinic_name,
                "contact": {
                    "phone": doctor.contact.phone,
                    "email": doctor.contact.email,
                },
                "languages": doctor.languages,
                "availability": doctor.availability.model_dump() if hasattr(doctor.availability, 'model_dump') else doctor.availability.dict() if hasattr(doctor.availability, 'dict') else str(doctor.availability),
                "blocked_dates": doctor.blocked_dates if hasattr(doctor, 'blocked_dates') else [],
                "appointment_duration_minutes": doctor.appointment_duration_minutes,
            }
            
            logger.info(f"Get doctor details: retrieved {doctor_id}")
            
            return result
        except Exception as e:
            logger.error(f"Error getting doctor details: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_clinic_details(self, clinic_id: str) -> Dict[str, Any]:
        """
        Get specific clinic details with all doctors.
        
        Args:
            clinic_id: The clinic ID
            
        Returns:
            Dict with complete clinic information and doctors list
        """
        try:
            clinic_data = get_clinic_with_doctors(clinic_id)
            
            if not clinic_data:
                return {
                    "success": False,
                    "error": f"Clinic with ID {clinic_id} not found"
                }
            
            clinic = clinic_data["clinic"]
            doctors = clinic_data["doctors"]
            
            # Convert to dict format
            result = {
                "success": True,
                "id": clinic.id,
                "name": clinic.name,
                "address": {
                    "street": clinic.address.street,
                    "area": clinic.address.area,
                    "city": clinic.address.city,
                    "state": clinic.address.state,
                    "pincode": clinic.address.pincode,
                    "country": clinic.address.country,
                },
                "contact": {
                    "phone": clinic.contact.phone,
                    "email": clinic.contact.email,
                    "emergency": clinic.contact.emergency,
                },
                "specialties": clinic.specialties,
                "operating_hours": clinic.operating_hours.dict() if hasattr(clinic.operating_hours, 'dict') else str(clinic.operating_hours),
                "appointment_duration_minutes": clinic.appointment_duration_minutes,
                "timezone": clinic.timezone,
                "doctor_count": len(doctors),
                "doctors": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "title": d.title,
                        "specialty": d.specialty,
                        "consultation_fee": d.consultation_fee,
                        "experience_years": d.experience_years,
                    }
                    for d in doctors
                ],
            }
            
            logger.info(f"Get clinic details: retrieved {clinic_id} with {len(doctors)} doctors")
            
            return result
        except Exception as e:
            logger.error(f"Error getting clinic details: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_booking_readiness(
        self,
        doctor_id: Optional[str] = None,
        clinic_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        patient_phone: Optional[str] = None,
        patient_email: Optional[str] = None,
        appointment_date: Optional[str] = None,
        appointment_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check if all required information is collected for booking.
        
        Args:
            All booking fields (optional)
            
        Returns:
            Dict with validation results and missing fields
        """
        try:
            booking_data = {
                "doctor_id": doctor_id,
                "clinic_id": clinic_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "patient_email": patient_email,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
            }
            
            validation = validate_booking_data(booking_data)
            
            logger.info(f"Booking readiness check: valid={validation['valid']}, missing={validation['missing_fields']}")
            
            return {
                "success": True,
                "ready": validation["valid"],
                "missing_fields": validation["missing_fields"],
                "errors": validation["errors"],
                "message": (
                    "All required information is collected. Ready to book!"
                    if validation["valid"]
                    else f"Missing required fields: {', '.join(validation['missing_fields'])}"
                )
            }
        except Exception as e:
            logger.error(f"Error checking booking readiness: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _book_appointment(
        self,
        doctor_id: str,
        clinic_id: str,
        patient_name: str,
        patient_phone: str,
        patient_email: str,
        appointment_date: str,
        appointment_time: str,
        patient_age: Optional[int] = None,
        patient_notes: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Book an appointment.
        
        Args:
            All required booking fields
            
        Returns:
            Dict with booking result
        """
        logger.info(f"🎯 _book_appointment called with args:")
        logger.info(f"   doctor_id={doctor_id}, clinic_id={clinic_id}")
        logger.info(f"   patient_name={patient_name}, patient_phone={patient_phone}, patient_email={patient_email}")
        logger.info(f"   appointment_date={appointment_date}, appointment_time={appointment_time}")
        print(f"[BOOK_APPOINTMENT] Tool called with: doctor_id={doctor_id}, patient={patient_name}, date={appointment_date}, time={appointment_time}")
        
        try:
            # Validate first
            booking_data = {
                "doctor_id": doctor_id,
                "clinic_id": clinic_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "patient_email": patient_email,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
            }
            
            validation = validate_booking_data(booking_data)
            
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Missing required information",
                    "missing_fields": validation["missing_fields"],
                    "errors": validation["errors"],
                    "message": f"To complete booking, I need: {', '.join(validation['missing_fields'])}"
                }
            
            # Parse date and time
            try:
                parsed_date = date.fromisoformat(appointment_date)
                parsed_time = time.fromisoformat(appointment_time)
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid date or time format: {str(e)}. Date must be YYYY-MM-DD, time must be HH:MM"
                }
            
            # Create appointment
            logger.info(f"📞 Calling create_appointment function...")
            print(f"[BOOK_APPOINTMENT] Calling create_appointment function")
            result = await create_appointment(
                doctor_id=doctor_id,
                clinic_id=clinic_id,
                patient_name=patient_name,
                patient_phone=patient_phone,
                patient_email=patient_email,
                appointment_date=parsed_date,
                appointment_time=parsed_time,
                patient_age=patient_age,
                patient_notes=patient_notes,
                notes=notes,
            )
            
            logger.info(f"📋 Book appointment result: success={result.get('success')}, appointment_id={result.get('appointment_id')}")
            logger.info(f"📋 Full result: {result}")
            print(f"[BOOK_APPOINTMENT] Result: success={result.get('success')}, appointment_id={result.get('appointment_id')}")
            print(f"[BOOK_APPOINTMENT] Full result dict: {result}")
            if result.get('error'):
                print(f"[BOOK_APPOINTMENT] ❌ ERROR: {result.get('error')}")
                print(f"[BOOK_APPOINTMENT] Error type: {result.get('error_type', 'Unknown')}")
            if result.get('missing_fields'):
                print(f"[BOOK_APPOINTMENT] Missing fields: {result.get('missing_fields')}")
            if not result.get('success'):
                logger.error(f"Appointment booking failed: {result.get('error')}")
                logger.error(f"Error type: {result.get('error_type', 'Unknown')}")
                logger.error(f"Full error details: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error booking appointment: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to book appointment: {str(e)}"
            }
    
    async def _get_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """
        Get appointment by ID.
        
        Args:
            appointment_id: Appointment ID
            
        Returns:
            Dict with appointment details
        """
        try:
            appointment = await get_appointment_by_id(appointment_id)
            
            if not appointment:
                return {
                    "success": False,
                    "error": f"Appointment {appointment_id} not found"
                }
            
            logger.info(f"Retrieved appointment: {appointment_id}")
            
            return {
                "success": True,
                "appointment": appointment
            }
            
        except Exception as e:
            logger.error(f"Error getting appointment {appointment_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _find_appointments(
        self,
        patient_name: Optional[str] = None,
        patient_phone: Optional[str] = None,
        appointment_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find appointments by various criteria.
        
        Args:
            patient_name: Patient name to search
            patient_phone: Patient phone to search
            appointment_date: Date to search (YYYY-MM-DD)
            
        Returns:
            Dict with list of appointments
        """
        try:
            appointments = []
            
            if appointment_date:
                # Search by date
                try:
                    parsed_date = date.fromisoformat(appointment_date)
                    date_appointments = await get_appointments_by_date(parsed_date)
                    appointments.extend(date_appointments)
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid date format: {appointment_date}. Must be YYYY-MM-DD"
                    }
            
            if patient_phone:
                # Search by phone
                phone_appointments = await get_appointments_by_patient_phone(patient_phone)
                appointments.extend(phone_appointments)
            
            if patient_name:
                # Search by name
                name_appointments = await get_appointments_by_patient_name(patient_name)
                appointments.extend(name_appointments)
            
            # Remove duplicates (by appointment_id)
            seen_ids = set()
            unique_appointments = []
            for apt in appointments:
                apt_id = apt.get("appointment_id")
                if apt_id and apt_id not in seen_ids:
                    seen_ids.add(apt_id)
                    unique_appointments.append(apt)
            
            # Sort by date (most recent first)
            unique_appointments.sort(
                key=lambda x: x.get("date", ""),
                reverse=True
            )
            
            logger.info(f"Found {len(unique_appointments)} appointments")
            
            return {
                "success": True,
                "count": len(unique_appointments),
                "appointments": unique_appointments
            }
            
        except Exception as e:
            logger.error(f"Error finding appointments: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "count": 0,
                "appointments": []
            }
    
    async def _cancel_appointment(
        self,
        appointment_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel an appointment.
        
        Args:
            appointment_id: Appointment ID to cancel
            reason: Optional cancellation reason
            
        Returns:
            Dict with cancellation result
        """
        try:
            result = await cancel_appointment_func(appointment_id, reason)
            
            logger.info(f"Cancel appointment result: success={result.get('success')}, appointment_id={appointment_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to cancel appointment: {str(e)}"
            }


# Global instance
_tool_executor = ToolExecutor()


def get_tool_executor() -> ToolExecutor:
    """Get the global tool executor instance."""
    return _tool_executor

