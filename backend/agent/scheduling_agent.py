# Scheduling agent implementation
from typing import Optional
from backend.models.schemas import MessageResponse, TextMessageData, ActionMessageData
import json
import os

async def get_agent_response(message: str, conversation_id: Optional[str] = None) -> MessageResponse:
    """
    Process user message and return structured response.
    This is a simplified implementation - you can integrate with your LLM here.
    """
    message_lower = message.lower()
    
    # Example: If user asks about availability, return action message with time slots
    if any(keyword in message_lower for keyword in ['available', 'time', 'slot', 'schedule', 'when']):
        # Load available time slots (example)
        try:
            schedule_path = os.path.join(os.path.dirname(__file__), '../../data/doctor_schedule.json')
            with open(schedule_path, 'r') as f:
                schedule = json.load(f)
            
            # Extract available slots (this is a simplified example)
            # In a real implementation, you'd process the schedule and get available slots
            available_slots = [
                {"label": "Monday, 9:00 AM", "value": "2024-01-15T09:00:00"},
                {"label": "Monday, 2:00 PM", "value": "2024-01-15T14:00:00"},
                {"label": "Tuesday, 10:00 AM", "value": "2024-01-16T10:00:00"},
                {"label": "Wednesday, 3:00 PM", "value": "2024-01-17T15:00:00"},
            ]
            
            return MessageResponse(
                msg_type="action1",
                data=ActionMessageData(
                    msg_body="Here are the available time slots. Please select one:",
                    action=available_slots
                )
            )
        except Exception:
            # Fallback to text message if schedule can't be loaded
            return MessageResponse(
                msg_type="text",
                data=TextMessageData(
                    msg_body="I'm checking available time slots for you. Please wait a moment."
                )
            )
    
    # Default: return text message
    return MessageResponse(
        msg_type="text",
        data=TextMessageData(
            msg_body="I understand. How can I help you schedule an appointment?"
        )
    )
