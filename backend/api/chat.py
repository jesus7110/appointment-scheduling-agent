"""
Chat API endpoint for the appointment scheduling agent.

Handles user messages and generates responses using the LLM.
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging
from datetime import date

from models.schemas import ChatRequest, ChatResponse, ChatMessage, BotMessage, BotMessageData
from agent.model_client import get_model_client
from utils.data_loader import (
    get_summary_stats,
    get_all_specialties,
    load_general_info,
    get_doctors_by_specialty,
    load_doctors,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["chat"])


def build_system_prompt() -> str:
    """
    Build the system prompt with clinic/doctor context.
    
    Returns:
        System prompt string with current data context.
    """
    try:
        # Get current data stats
        stats = get_summary_stats()
        specialties = get_all_specialties()
        general_info = load_general_info()
        
        system_prompt = f"""You are a helpful medical appointment scheduling assistant for clinics in New Delhi, India.

**Your Role:**
- Help patients find doctors and book appointments
- Answer questions about clinics, doctors, and specialties
- Be friendly, professional, and patient-focused
- Use Indian English and be culturally appropriate

**Available Resources:**
- Total Clinics: {stats['total_clinics']} across New Delhi
- Total Doctors: {stats['total_doctors']} doctors
- Specialties Available: {', '.join(specialties[:10])}{'...' if len(specialties) > 10 else ''}
- Cities: {', '.join(stats['cities'])}
- Average Consultation Fee: ₹{stats['average_consultation_fee']:.0f}

**Booking Policies:**
- Advance booking: Up to {general_info.booking_advance_days} days
- Cancellation: At least {general_info.cancellation_hours} hours before appointment
- Emergency Contact: {general_info.emergency_contact}

**Instructions:**
1. Greet patients warmly
2. Ask about their needs (specialty, preferred location, date/time)
3. Provide relevant information about doctors and clinics
4. For now, provide information only (booking functionality coming soon)
5. Be concise but informative
6. Use ₹ symbol for fees (Indian Rupees)

**Important:**
- Always mention this is for New Delhi, India
- Consultation fees are in Indian Rupees (₹)
- Working hours follow Indian Standard Time (IST)
"""
        return system_prompt
        
    except Exception as e:
        logger.error(f"Error building system prompt: {e}")
        # Fallback to basic prompt
        return """You are a helpful medical appointment scheduling assistant. 
Help patients find doctors and book appointments. Be friendly and professional."""


def build_action_bot_message(
    request: ChatRequest,
    assistant_text: str
) -> BotMessage:
    """
    Optionally build an action-style bot message (buttons) based on user intent.

    Heuristics:
    - If user asks to book/schedule/choose time/slot -> return time-slot buttons.
    - If user mentions doctor/specialist or a specialty -> return doctor selection buttons.
    """
    try:
        last_user_msg = (request.messages[-1].content or "").lower()

        # Detect time/slot intent
        time_keywords = ["slot", "time", "schedule", "book", "appointment", "available", "availability"]
        wants_time = any(k in last_user_msg for k in time_keywords)

        # Detect specialty intent
        specialty = None
        for spec in get_all_specialties():
            if spec.lower() in last_user_msg:
                specialty = spec
                break

        doctor_keywords = ["doctor", "dr", "specialist", "consult", "physician"]
        wants_doctor = specialty is not None or any(k in last_user_msg for k in doctor_keywords)

        # Build time slot actions
        if wants_time:
            today = date.today()
            times = ["09:00", "11:00", "14:00", "16:00"]
            actions = [
                {
                    "key": f"{t} today",
                    "value": f"{today.isoformat()}T{t}:00"
                } for t in times
            ]
            msg_body = assistant_text or "Please choose a time slot:"
            return BotMessage(
                msg_type="action1",
                data=BotMessageData(
                    msg_body=msg_body,
                    action=actions
                )
            )

        # Build doctor selection actions
        if wants_doctor:
            doctors = get_doctors_by_specialty(specialty) if specialty else load_doctors()
            actions = [
                {
                    "key": f"{doc.name} ({doc.clinic_name})",
                    "value": doc.id
                }
                for doc in doctors[:4]
            ]
            if actions:
                msg_body = assistant_text or "Please select a doctor:"
                return BotMessage(
                    msg_type="action1",
                    data=BotMessageData(
                        msg_body=msg_body,
                        action=actions
                    )
                )

        return None
    except Exception as e:
        logger.warning(f"Failed to build action bot message: {e}")
        return None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Handle chat messages and generate responses.
    
    Args:
        request: ChatRequest with messages and optional session_id
    
    Returns:
        ChatResponse with assistant's reply
    
    Raises:
        HTTPException: If request is invalid or LLM fails
    """
    try:
        # Validate request
        if not request.messages:
            raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
        # Get the model client
        model_client = get_model_client()
        
        # Build system prompt with context
        system_prompt = build_system_prompt()
        
        # Prepare messages for LLM
        # Note: Gemini doesn't support "system" role, so we prepend it to the first user message
        llm_messages = []
        
        # Add conversation history
        for i, msg in enumerate(request.messages):
            # For the first user message, prepend the system prompt
            if i == 0 and msg.role == "user":
                content = f"{system_prompt}\n\n---\n\nUser: {msg.content}"
                llm_messages.append({
                    "role": "user",
                    "content": content
                })
            else:
                llm_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        logger.info(f"Processing chat request with {len(request.messages)} messages")
        
        # Generate response from LLM
        assistant_text = await model_client.generate_chat(
            messages=llm_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        logger.info(f"Generated response: {len(assistant_text)} characters")

        # Build structured bot message for the frontend (with optional actions)
        bot_message = build_action_bot_message(request, assistant_text)
        if not bot_message:
            bot_message = BotMessage(
                msg_type="text",
                data=BotMessageData(msg_body=assistant_text)
            )
        
        # Build response
        response = ChatResponse(
            message=assistant_text,
            bot_message=bot_message,
            session_id=request.session_id,
            suggested_actions=None,
            appointment_summary=None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Health check for chat API."""
    return {
        "status": "ok",
        "service": "chat",
        "model_configured": True
    }


@router.get("/context")
async def get_context():
    """
    Get current clinic/doctor context (for debugging/testing).
    
    Returns:
        Current stats and available data
    """
    try:
        stats = get_summary_stats()
        specialties = get_all_specialties()
        general_info = load_general_info()
        
        return {
            "status": "ok",
            "data": {
                "total_clinics": stats['total_clinics'],
                "total_doctors": stats['total_doctors'],
                "specialties": specialties,
                "cities": stats['cities'],
                "average_fee": stats['average_consultation_fee'],
                "booking_policies": {
                    "advance_days": general_info.booking_advance_days,
                    "cancellation_hours": general_info.cancellation_hours,
                    "timezone": general_info.timezone
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))
