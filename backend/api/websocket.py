"""
WebSocket endpoint for real-time chat communication.

Handles bidirectional messaging between frontend and backend.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
import json
import asyncio

from models.schemas import BotMessage, BotMessageData, BotAction
from agent.model_client import get_model_client
from utils.session_manager import get_session_manager
from utils.data_loader import (
    get_summary_stats,
    get_all_specialties,
    load_general_info,
    search_doctors,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


def build_system_prompt() -> str:
    """Build the system prompt with clinic/doctor context."""
    try:
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
        return "You are a helpful medical appointment scheduling assistant."


async def process_message(session_id: str, user_message: str) -> dict:
    """
    Process a user message and generate a response with tool calling support.
    
    Args:
        session_id: The session ID
        user_message: The user's message
        
    Returns:
        Response dict with bot_message and optional close_connection flag
    """
    from tools.tool_definitions import get_test_tools
    from tools.tool_executor import get_tool_executor
    
    session_manager = get_session_manager()
    model_client = get_model_client()
    tool_executor = get_tool_executor()
    
    # Add user message to history
    session_manager.add_message(session_id, "user", user_message)
    
    # Get conversation history
    history = session_manager.get_messages(session_id)
    
    # Build system prompt
    system_prompt = build_system_prompt()
    
    # Update system prompt to mention tools
    system_prompt += """

**IMPORTANT - Available Tools:**
You have access to tools that can perform actions. When appropriate, use these tools:
- end_conversation: When user wants to hang up, end chat, say goodbye, or disconnect
"""
    
    # Prepare messages for LLM (prepend system prompt to first message)
    llm_messages = []
    for i, msg in enumerate(history):
        if i == 0 and msg["role"] == "user":
            content = f"{system_prompt}\n\n---\n\nUser: {msg['content']}"
            llm_messages.append({"role": "user", "content": content})
        else:
            llm_messages.append({"role": msg["role"], "content": msg["content"]})
    
    logger.info(f"Processing message for session {session_id} ({len(history)} messages in history)")
    
    # Get available tools
    tools = get_test_tools()
    
    # First LLM call with tools
    response = await model_client.generate_chat_with_tools(
        messages=llm_messages,
        tools=tools,
        temperature=0.7,
        max_tokens=1000
    )
    
    # Check if LLM wants to use tools
    should_close_connection = False
    if 'tool_calls' in response and response['tool_calls']:
        logger.info(f"LLM requested {len(response['tool_calls'])} tool calls")
        
        # Add assistant message with tool calls to history
        assistant_message = {
            "role": "assistant",
            "content": response.get('content', ""),
            "tool_calls": response['tool_calls']
        }
        llm_messages.append(assistant_message)
        
        # Execute each tool call
        for tool_call in response['tool_calls']:
            tool_name = tool_call['function']['name']
            tool_args = json.loads(tool_call['function']['arguments'])
            
            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
            
            # Execute the tool
            tool_result = tool_executor.execute_tool(tool_name, tool_args)
            
            # Check if tool wants to close connection
            if tool_result.get('action') == 'close_connection':
                should_close_connection = True
                assistant_text = tool_result.get('message', 'Goodbye!')
            else:
                # Add tool result to messages for LLM to process
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "content": json.dumps(tool_result)
                }
                llm_messages.append(tool_message)
                
                # Second LLM call with tool results
                final_response = await model_client.generate_chat(
                    messages=llm_messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                assistant_text = final_response
    else:
        # No tools needed, use response as-is
        assistant_text = response.get('content', '')
    
    # Add assistant response to history
    session_manager.add_message(session_id, "assistant", assistant_text)
    
    # Build bot message
    bot_message = {
        "msg_type": "text",
        "data": {
            "msg_body": assistant_text
        }
    }
    
    result = {
        "type": "message",
        "bot_message": bot_message,
        "session_id": session_id
    }
    
    # Add close flag if needed
    if should_close_connection:
        result["close_connection"] = True
    
    return result


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time chat.
    
    Query params:
        client_id: Optional client ID (if reconnecting)
        session_id: Optional session ID (if resuming conversation)
    """
    await websocket.accept()
    
    session_manager = get_session_manager()
    
    try:
        # Register or get client
        if not client_id:
            client_id = session_manager.register_client()
        else:
            client_id = session_manager.register_client(client_id)
        
        # Send client_id to frontend
        await websocket.send_json({
            "type": "client_registered",
            "client_id": client_id
        })
        
        # Create or resume session
        if not session_id or not session_manager.get_session(session_id):
            session_id = session_manager.create_session(client_id)
            await websocket.send_json({
                "type": "session_created",
                "session_id": session_id
            })
        else:
            await websocket.send_json({
                "type": "session_resumed",
                "session_id": session_id
            })
        
        # Register WebSocket connection
        session_manager.register_connection(session_id, websocket)
        
        logger.info(f"WebSocket connected: client={client_id}, session={session_id}")
        
        # Send welcome message only for new sessions (no existing messages)
        session = session_manager.get_session(session_id)
        if session and len(session["messages"]) == 0:
            welcome_message = {
                "type": "message",
                "bot_message": {
                    "msg_type": "text",
                    "data": {
                        "msg_body": "Hello! I'm here to help you schedule an appointment. How can I assist you today?"
                    }
                }
            }
            await websocket.send_json(welcome_message)
        
        # Message loop with inactivity timeout
        INACTIVITY_TIMEOUT = 60  # 1 minute in seconds
        
        while True:
            try:
                # Receive message from client with timeout
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=INACTIVITY_TIMEOUT
                )
                
                message_type = data.get("type")
                
                if message_type == "message":
                    # User sent a message
                    user_message = data.get("content", "")
                    
                    if user_message.strip():
                        # Send typing indicator
                        await websocket.send_json({"type": "typing", "is_typing": True})
                        
                        # Process message and generate response
                        response = await process_message(session_id, user_message)
                        
                        # Send response
                        await websocket.send_json(response)
                        
                        # Check if tool requested connection close
                        if response.get("close_connection"):
                            logger.info(f"Tool requested connection close for session {session_id}")
                            # Give a brief moment for message delivery
                            await asyncio.sleep(0.5)
                            # Close the connection gracefully
                            await websocket.close(code=1000, reason="User ended conversation")
                            break  # Exit the message loop
                
                elif message_type == "ping":
                    # Keep-alive ping
                    await websocket.send_json({"type": "pong"})
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    
            except asyncio.TimeoutError:
                # Inactivity timeout reached - disconnect user
                logger.info(f"Inactivity timeout for session {session_id}")
                try:
                    await websocket.send_json({
                        "type": "inactivity_timeout",
                        "message": "You've been disconnected due to inactivity."
                    })
                    # Give a brief moment for message to be sent, then close
                    await asyncio.sleep(0.1)
                    await websocket.close(code=1000, reason="Inactivity timeout")
                except:
                    pass
                break  # Exit the loop and close connection
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "An error occurred. Please try reconnecting."
            })
        except:
            pass
    finally:
        # Cleanup
        session_manager.unregister_connection(session_id)
        logger.info(f"WebSocket connection closed: session={session_id}")


@router.get("/api/client/register")
async def register_client(client_id: Optional[str] = Query(None)):
    """
    Register a client and get a client_id.
    
    For clients that prefer REST for initial setup.
    """
    session_manager = get_session_manager()
    client_id = session_manager.register_client(client_id)
    
    return {
        "client_id": client_id,
        "status": "registered"
    }


@router.get("/api/sessions/stats")
async def get_session_stats():
    """Get session manager statistics (for debugging)."""
    session_manager = get_session_manager()
    return session_manager.get_stats()

