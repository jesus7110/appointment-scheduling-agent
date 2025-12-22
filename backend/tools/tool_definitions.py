"""
Tool/Function definitions for LLM function calling.

These define what tools the LLM can use to interact with the system.
"""

from typing import List, Dict, Any

# Tool: End conversation
END_CONVERSATION_TOOL = {
    "type": "function",
    "function": {
        "name": "end_conversation",
        "description": "End the conversation and close the connection. Use this when the user wants to hang up, end the chat, say goodbye, or disconnect. The system will send a goodbye message and close the WebSocket connection.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Optional reason for ending the conversation (e.g., 'User said goodbye', 'User wants to hang up')"
                }
            },
            "required": []
        }
    }
}

# Tool 1: Search for doctors
SEARCH_DOCTORS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_doctors",
        "description": "Search for doctors by name, specialty, location, maximum consultation fee, and language. Returns a list of matching doctors with their details. Use this when user mentions a specific doctor name or wants to find doctors by criteria.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Doctor name to search for (e.g., 'Dr. Anil Gupta', 'Anil', 'Nisha'). Case-insensitive partial match. Use this when user mentions a specific doctor name."
                },
                "specialty": {
                    "type": "string",
                    "description": "Medical specialty to filter by (e.g., 'Cardiology', 'Orthopedics', 'Pediatrics'). Case-insensitive partial match."
                },
                "max_fee": {
                    "type": "integer",
                    "description": "Maximum consultation fee in Indian Rupees (₹). Only return doctors whose fee is less than or equal to this amount."
                },
                "language": {
                    "type": "string",
                    "description": "Preferred language spoken by doctor (e.g., 'Hindi', 'English', 'Gujarati')"
                },
                "clinic_id": {
                    "type": "string",
                    "description": "Specific clinic ID to filter by (e.g., 'clinic-001')"
                }
            },
            "required": []
        }
    }
}

# Tool 2: Search for clinics
SEARCH_CLINICS_TOOL = {
    "type": "function",
    "function": {
        "name": "search_clinics",
        "description": "Search for clinics by location (city, area) and medical specialties offered. Returns clinic details including address, contact, and operating hours.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to filter by (e.g., 'New Delhi')"
                },
                "area": {
                    "type": "string",
                    "description": "Specific area/locality to filter by (e.g., 'Saket', 'Connaught Place', 'Vasant Kunj')"
                },
                "specialty": {
                    "type": "string",
                    "description": "Medical specialty offered at the clinic (e.g., 'Cardiology', 'Pediatrics')"
                }
            },
            "required": []
        }
    }
}

# Tool 3: Get specific doctor details
GET_DOCTOR_DETAILS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_doctor_details",
        "description": "Get detailed information about a specific doctor by their ID. Returns full doctor profile including qualifications, experience, fees, availability schedule, and clinic information.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {
                    "type": "string",
                    "description": "The unique doctor ID (e.g., 'doctor-001')"
                }
            },
            "required": ["doctor_id"]
        }
    }
}

# Tool 4: Get specific clinic details
GET_CLINIC_DETAILS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_clinic_details",
        "description": "Get detailed information about a specific clinic by its ID. Returns clinic information including address, contact, operating hours, specialties, and list of all doctors available at that clinic.",
        "parameters": {
            "type": "object",
            "properties": {
                "clinic_id": {
                    "type": "string",
                    "description": "The unique clinic ID (e.g., 'clinic-001')"
                }
            },
            "required": ["clinic_id"]
        }
    }
}

# Tool 5: Check booking readiness
CHECK_BOOKING_READINESS_TOOL = {
    "type": "function",
    "function": {
        "name": "check_booking_readiness",
        "description": "Check if all required information is collected to book an appointment. Use this before attempting to book to ensure you have all 7 required fields. Returns missing fields and validation errors.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {
                    "type": "string",
                    "description": "Doctor ID (e.g., 'doctor-001')"
                },
                "clinic_id": {
                    "type": "string",
                    "description": "Clinic ID (e.g., 'clinic-001')"
                },
                "patient_name": {
                    "type": "string",
                    "description": "Patient's full name"
                },
                "patient_phone": {
                    "type": "string",
                    "description": "Patient's phone number"
                },
                "patient_email": {
                    "type": "string",
                    "description": "Patient's email address"
                },
                "appointment_date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format (e.g., '2025-01-25')"
                },
                "appointment_time": {
                    "type": "string",
                    "description": "Appointment time in HH:MM format (e.g., '10:00')"
                }
            },
            "required": []
        }
    }
}

# Tool 6: Book appointment
BOOK_APPOINTMENT_TOOL = {
    "type": "function",
    "function": {
        "name": "book_appointment",
        "description": "Book an appointment with a doctor. Use this ONLY after all required information is collected and validated. Returns appointment ID and confirmation code.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {
                    "type": "string",
                    "description": "Doctor ID (e.g., 'doctor-001')"
                },
                "clinic_id": {
                    "type": "string",
                    "description": "Clinic ID (e.g., 'clinic-001')"
                },
                "patient_name": {
                    "type": "string",
                    "description": "Patient's full name"
                },
                "patient_phone": {
                    "type": "string",
                    "description": "Patient's phone number"
                },
                "patient_email": {
                    "type": "string",
                    "description": "Patient's email address"
                },
                "appointment_date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format (e.g., '2025-01-25')"
                },
                "appointment_time": {
                    "type": "string",
                    "description": "Appointment time in HH:MM format (e.g., '10:00')"
                },
                "patient_age": {
                    "type": "integer",
                    "description": "Optional patient age"
                },
                "patient_notes": {
                    "type": "string",
                    "description": "Optional patient medical notes"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional appointment notes"
                }
            },
            "required": ["doctor_id", "clinic_id", "patient_name", "patient_phone", "patient_email", "appointment_date", "appointment_time"]
        }
    }
}

# Tool 7: Get appointment by ID
GET_APPOINTMENT_TOOL = {
    "type": "function",
    "function": {
        "name": "get_appointment",
        "description": "Get appointment details by appointment ID. Use this when user provides an appointment ID or confirmation code.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "Appointment ID (e.g., 'APP-00001')"
                }
            },
            "required": ["appointment_id"]
        }
    }
}

# Tool 8: Find appointments
FIND_APPOINTMENTS_TOOL = {
    "type": "function",
    "function": {
        "name": "find_appointments",
        "description": "Find appointments by patient name, phone number, or date. Use this when user asks to see their appointments or check booking history.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_name": {
                    "type": "string",
                    "description": "Patient name to search for (partial match)"
                },
                "patient_phone": {
                    "type": "string",
                    "description": "Patient phone number to search for"
                },
                "appointment_date": {
                    "type": "string",
                    "description": "Appointment date in YYYY-MM-DD format"
                }
            },
            "required": []
        }
    }
}

# Tool 9: Cancel appointment
CANCEL_APPOINTMENT_TOOL = {
    "type": "function",
    "function": {
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment. Use this when user wants to cancel their booking.",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "Appointment ID to cancel (e.g., 'APP-00001')"
                },
                "reason": {
                    "type": "string",
                    "description": "Optional reason for cancellation"
                }
            },
            "required": ["appointment_id"]
        }
    }
}

# All available tools - starting with just end_conversation for testing
TEST_TOOLS = [
    END_CONVERSATION_TOOL
]

ALL_TOOLS = [
    END_CONVERSATION_TOOL,
    SEARCH_DOCTORS_TOOL,
    SEARCH_CLINICS_TOOL,
    GET_DOCTOR_DETAILS_TOOL,
    GET_CLINIC_DETAILS_TOOL,
    CHECK_BOOKING_READINESS_TOOL,
    BOOK_APPOINTMENT_TOOL,
    GET_APPOINTMENT_TOOL,
    FIND_APPOINTMENTS_TOOL,
    CANCEL_APPOINTMENT_TOOL,
]


def get_test_tools() -> List[Dict[str, Any]]:
    """Get test tools (just hang up for now)."""
    return TEST_TOOLS


def get_all_tools() -> List[Dict[str, Any]]:
    """Get all available tool definitions."""
    return ALL_TOOLS

