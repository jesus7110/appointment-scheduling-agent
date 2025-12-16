# Chat API endpoint
from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.models.schemas import ChatRequest, MessageResponse, TextMessageData, ActionMessageData
from backend.agent.scheduling_agent import get_agent_response

router = APIRouter()

@router.post("/chat", response_model=MessageResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that returns structured messages.
    Returns either text messages or action messages with interactive options.
    """
    try:
        # Get response from the scheduling agent
        # The agent should return structured data
        response = await get_agent_response(request.message, request.conversation_id)
        
        # Return the structured response
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
