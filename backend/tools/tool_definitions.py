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
        "description": "Search for doctors by specialty, location, maximum consultation fee, and language. Returns a list of matching doctors with their details.",
        "parameters": {
            "type": "object",
            "properties": {
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

# All available tools - starting with just end_conversation for testing
TEST_TOOLS = [
    END_CONVERSATION_TOOL
]

ALL_TOOLS = [
    END_CONVERSATION_TOOL,
    SEARCH_DOCTORS_TOOL,
    SEARCH_CLINICS_TOOL,
]


def get_test_tools() -> List[Dict[str, Any]]:
    """Get test tools (just hang up for now)."""
    return TEST_TOOLS


def get_all_tools() -> List[Dict[str, Any]]:
    """Get all available tool definitions."""
    return ALL_TOOLS

