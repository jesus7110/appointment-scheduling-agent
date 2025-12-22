"""
WebSocket endpoint for real-time chat communication.

Handles bidirectional messaging between frontend and backend.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
import json
import asyncio
import re
from datetime import datetime, timezone, timedelta

from models.schemas import BotMessage, BotMessageData, BotAction
from agent.model_client import get_model_client
from utils.session_manager import get_session_manager
from utils.data_loader import (
    get_summary_stats,
    get_all_specialties,
    load_general_info,
    search_doctors,
)
from database.db_service import (
    store_session_info_background,
    store_conversation_history_background,
    finalize_session_background,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


def get_indian_datetime() -> dict:
    """
    Get the current date and time in Indian Standard Time (IST).
    
    Returns:
        dict with 'date' and 'time' keys in formatted strings
    """
    # IST is UTC+5:30
    ist = timezone(timedelta(hours=5, minutes=30))
    current_time = datetime.now(ist)
    
    return {
        'date': current_time.strftime('%Y-%m-%d'),
        'time': current_time.strftime('%H:%M:%S'),
        'datetime': current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'day_name': current_time.strftime('%A'),
        'date_formatted': current_time.strftime('%B %d, %Y')
    }


def build_system_prompt() -> str:
    """Build the system prompt with clinic/doctor context."""
    try:
        stats = get_summary_stats()
        specialties = get_all_specialties()
        general_info = load_general_info()
        indian_time = get_indian_datetime()
        
        system_prompt = f"""Act as a medical appointment scheduling assistant, named Zoya for a group of clinics in New Delhi, India.

        Your Role:
        - Help patients find doctors and book appointments
        - Answer questions about clinics, doctors, and specialties
        - Users can ask query, book, modify, update get information about an appointment
        - Use Indian English and be culturally appropriate

        Current Date and Time (IST):
        - Today is {indian_time['day_name']}, {indian_time['date_formatted']}
        - Current time: {indian_time['time']} IST
        - Full datetime: {indian_time['datetime']}

        Available Resources:
        - Total Clinics: {stats['total_clinics']} across New Delhi
        - Total Doctors: {stats['total_doctors']} doctors
        - Specialties Available: {', '.join(specialties[:10])}{'...' if len(specialties) > 10 else ''}
        - Cities: {', '.join(stats['cities'])}
        - Average Consultation Fee: ₹{stats['average_consultation_fee']:.0f}

        Booking Policies:
        - Advance booking: Up to {general_info.booking_advance_days} days
        - Cancellation: At least {general_info.cancellation_hours} hours before appointment
        - Emergency Contact: {general_info.emergency_contact}

        Instructions:
        1. Greet patients warmly with just introduce yourself very concisely and "how can I help you" - no need to say anything else.
        2. Try to understand the user's needs and decide why they are here.
        3. you can ask onlyone question at a time.
        4. Provide relevant information about doctors and clinics
        5. Be concise, do not give over information at a time. 
        6. Use ₹ symbol for fees (Indian Rupees)
        7. When discussing dates and times, reference the current date/time above
        8. ALWAYS use tools to verify information - never rely on memory alone
        9. When user mentions a doctor name, use search_doctors with name parameter to find that specific doctor
        10. After providing information, always guide the user on the next step clearly
        11. Be proactive and helpful - provide clear guidance on what to do next

        Important:
        - Always mention this is for New Delhi, India
        - Consultation fees are in Indian Rupees (₹)
        - Working hours follow Indian Standard Time (IST)
        - Current date and time are provided above - use this context when discussing appointment availability


        What not to do:
        - do not use ** in your response.
        - do not use * in your response.
        - do not use _ in your response.
        - do not use ` in your response.
        - do not use ``` in your response.
        - do not use ```python in your response.
        - do not use ```json in your response.
        - do not use ```html in your response.
        - do not use ```css in your response.
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
    from tools.tool_definitions import get_all_tools
    from tools.tool_executor import get_tool_executor
    
    session_manager = get_session_manager()
    model_client = get_model_client()
    tool_executor = get_tool_executor()
    
    # Get session info before adding message (for message_order calculation)
    session = session_manager.get_session(session_id)
    client_id = session.get("client_id") if session else None
    message_order = len(session.get("messages", [])) if session else 0
    
    # Add user message to history
    session_manager.add_message(session_id, "user", user_message)
    
    # Store conversation history in database (async, non-blocking)
    if client_id:
        store_conversation_history_background(
            session_id=session_id,
            client_id=client_id,
            role="user",
            content=user_message,
            message_order=message_order + 1,  # +1 because we just added the message
        )
    
    # Get conversation history
    history = session_manager.get_messages(session_id)
    
    # Build system prompt
    system_prompt = build_system_prompt()
    
    # Update system prompt to mention tools
    system_prompt += """

**IMPORTANT - Available Tools:**
You have access to tools that can perform actions. When appropriate, use these tools:

**Discovery Tools:**
- search_doctors: Search for doctors by name, specialty, fee, language, or location. 
  * Use with name parameter when user mentions a specific doctor (e.g., "Dr. Anil", "Anil Gupta")
  * Use with specialty when user describes symptoms or needs (e.g., "chest pain" → Cardiology)
  * ALWAYS use this tool instead of making up doctor names or relying on memory
- search_clinics: When user wants to find clinics by area, city, or specialty
- get_doctor_details: When user asks about a specific doctor or wants detailed information after searching. Use doctor_id from search results.
- get_clinic_details: When user asks about a specific clinic or wants to see all doctors at a clinic

**Booking Tools:**
- check_booking_readiness: Check if all required information is collected before booking. Use this to verify you have all 7 required fields.
- book_appointment: Book an appointment. Use ONLY after all required fields are collected and validated.
- get_appointment: Get appointment details by appointment ID or confirmation code
- find_appointments: Find appointments by patient name, phone, or date
- cancel_appointment: Cancel an existing appointment

**Session Tools:**
- end_conversation: When user wants to hang up, end chat, say goodbye, or disconnect

**CRITICAL RULES:**
1. ALWAYS use tools to verify information - never rely on conversation memory alone
2. When user mentions a doctor name, use search_doctors with name parameter to find that specific doctor
3. When user selects a doctor from search results, use get_doctor_details with the doctor_id to get complete information
4. To book an appointment, you MUST collect these 7 fields: doctor_id, clinic_id, patient_name, patient_phone, patient_email, appointment_date, appointment_time
5. Before booking, use check_booking_readiness to verify all fields are present
6. Only call book_appointment when all required fields are validated
7. If any field is missing, ask the user specifically for that field
8. After providing information or completing an action, ALWAYS provide clear guidance on the next step
9. Be proactive: Guide users through the booking process step by step
10. When presenting doctor options, ask "Which doctor would you like to book with?" to guide next step
11. After user selects a doctor, ask "What date would you like to book for?" to guide next step
12. After user provides date, ask "What time would you prefer?" to guide next step
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
    
    # Get available tools - use ALL_TOOLS now
    tools = get_all_tools()
    
    # First LLM call with tools
    response = await model_client.generate_chat_with_tools(
        messages=llm_messages,
        tools=tools,
        temperature=0.7,
        max_tokens=1000
    )
    
    logger.info(f"LLM response keys: {response.keys()}")
    raw_content = response.get('content', '')
    logger.info(f"LLM response content preview: {str(raw_content)[:200]}")
    logger.info(f"Tool calls in response: {response.get('tool_calls', [])}")
    
    # Check if tool calls are in content but weren't parsed (Kimi format issue)
    # This needs to happen BEFORE we check the tool_calls field
    tool_calls_from_content = []
    if raw_content and "<|tool_calls_section_begin|>" in raw_content:
        logger.warning("Tool call tokens found in FIRST response content. Attempting to parse manually.")
        # Manual parsing
        pattern = r'<\|tool_calls_section_begin\|>(.*?)<\|tool_calls_section_end\|>'
        match = re.search(pattern, raw_content, re.DOTALL)
        if match:
            tool_calls_section = match.group(1)
            tool_call_pattern = r'<\|tool_call_begin\|>functions\.([^:]+):\d+<\|tool_call_argument_begin\|>(.*?)<\|tool_call_end\|>'
            tool_call_matches = re.finditer(tool_call_pattern, tool_calls_section, re.DOTALL)
            
            for idx, tool_match in enumerate(tool_call_matches):
                function_name = tool_match.group(1)
                arguments_str = tool_match.group(2).strip()
                try:
                    arguments = json.loads(arguments_str)
                    tool_calls_from_content.append({
                        'id': f"call_{idx}_{function_name}",
                        'type': 'function',
                        'function': {
                            'name': function_name,
                            'arguments': json.dumps(arguments, ensure_ascii=False)
                        }
                    })
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse tool call arguments for {function_name}: {e}")
        
        if tool_calls_from_content:
            logger.info(f"Successfully parsed {len(tool_calls_from_content)} tool calls from content tokens")
            # Clean the content
            cleaned_content = re.sub(pattern, '', raw_content, flags=re.DOTALL).strip()
            cleaned_content = re.sub(r'<\|tool_call[^|]*\|>', '', cleaned_content).strip()
            response['content'] = cleaned_content
            response['tool_calls'] = tool_calls_from_content
    
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
            
            logger.info(f"🚀 Executing tool: {tool_name} with args: {tool_args}")
            print(f"[TOOL_EXECUTION] Starting execution of tool: {tool_name}")
            print(f"[TOOL_EXECUTION] Tool args: {tool_args}")
            
            # Execute the tool (handles both sync and async)
            tool_result = await tool_executor.execute_tool(tool_name, tool_args)
            
            logger.info(f"✅ Tool {tool_name} execution completed")
            logger.info(f"📊 Tool result: success={tool_result.get('success')}, error={tool_result.get('error')}")
            print(f"[TOOL_EXECUTION] Tool {tool_name} result: success={tool_result.get('success')}")
            if tool_result.get('appointment_id'):
                logger.info(f"🎉 Appointment created: {tool_result.get('appointment_id')}")
                print(f"[TOOL_EXECUTION] ✅ Appointment ID: {tool_result.get('appointment_id')}")
            if tool_result.get('error'):
                logger.error(f"❌ Tool error: {tool_result.get('error')}")
                print(f"[TOOL_EXECUTION] ❌ Error: {tool_result.get('error')}")
            
            # Check if tool wants to close connection
            if tool_result.get('action') == 'close_connection':
                should_close_connection = True
                assistant_text = tool_result.get('message', 'Goodbye!')
                break  # Exit loop if connection should close
            else:
                # Add tool result to messages for LLM to process
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "content": json.dumps(tool_result, default=str, ensure_ascii=False)
                }
                llm_messages.append(tool_message)
                logger.info(f"Added tool result to messages for LLM processing")
        
        # If we didn't close connection, get final response from LLM
        if not should_close_connection:
            # Second LLM call with tool results
            final_response = await model_client.generate_chat(
                messages=llm_messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Check if final response contains tool calls (LLM might want to call another tool)
            if final_response and "<|tool_calls_section_begin|>" in final_response:
                logger.warning("Tool call tokens found in FINAL response. Attempting to parse and execute.")
                # Parse tool calls from final response
                pattern = r'<\|tool_calls_section_begin\|>(.*?)<\|tool_calls_section_end\|>'
                match = re.search(pattern, final_response, re.DOTALL)
                if match:
                    tool_calls_section = match.group(1)
                    tool_call_pattern = r'<\|tool_call_begin\|>functions\.([^:]+):\d+<\|tool_call_argument_begin\|>(.*?)<\|tool_call_end\|>'
                    tool_call_matches = re.finditer(tool_call_pattern, tool_calls_section, re.DOTALL)
                    
                    final_tool_calls = []
                    for idx, tool_match in enumerate(tool_call_matches):
                        function_name = tool_match.group(1)
                        arguments_str = tool_match.group(2).strip()
                        try:
                            arguments = json.loads(arguments_str)
                            final_tool_calls.append({
                                'id': f"call_final_{idx}_{function_name}",
                                'type': 'function',
                                'function': {
                                    'name': function_name,
                                    'arguments': json.dumps(arguments, ensure_ascii=False)
                                }
                            })
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse tool call arguments for {function_name}: {e}")
                    
                    if final_tool_calls:
                        logger.info(f"Found {len(final_tool_calls)} tool calls in final response. Executing them.")
                        # Execute the tool calls
                        for tool_call in final_tool_calls:
                            tool_name = tool_call['function']['name']
                            tool_args = json.loads(tool_call['function']['arguments'])
                            
                            logger.info(f"🚀 Executing tool from final response: {tool_name} with args: {tool_args}")
                            print(f"[TOOL_EXECUTION] Executing tool from final response: {tool_name}")
                            
                            tool_result = await tool_executor.execute_tool(tool_name, tool_args)
                            
                            logger.info(f"✅ Tool {tool_name} execution completed")
                            logger.info(f"📊 Tool result: success={tool_result.get('success')}, error={tool_result.get('error')}")
                            print(f"[TOOL_EXECUTION] Tool {tool_name} result: success={tool_result.get('success')}")
                            if tool_result.get('error'):
                                logger.error(f"❌ Tool {tool_name} error: {tool_result.get('error')}")
                                print(f"[TOOL_EXECUTION] ❌ Error: {tool_result.get('error')}")
                                if tool_result.get('error_type'):
                                    print(f"[TOOL_EXECUTION] Error type: {tool_result.get('error_type')}")
                            if tool_result.get('appointment_id'):
                                logger.info(f"🎉 Appointment created: {tool_result.get('appointment_id')}")
                                print(f"[TOOL_EXECUTION] ✅ Appointment ID: {tool_result.get('appointment_id')}")
                            
                            # Add tool result to messages
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call['id'],
                                "content": json.dumps(tool_result, default=str, ensure_ascii=False)
                            }
                            llm_messages.append(tool_message)
                        
                        # Get final response after executing tools from final response
                        cleaned_final = re.sub(pattern, '', final_response, flags=re.DOTALL).strip()
                        cleaned_final = re.sub(r'<\|tool_call[^|]*\|>', '', cleaned_final).strip()
                        
                        if cleaned_final:
                            assistant_text = cleaned_final
                        else:
                            # Get a new response from LLM with tool results
                            assistant_text = await model_client.generate_chat(
                                messages=llm_messages,
                                temperature=0.7,
                                max_tokens=1000
                            )
                    else:
                        # Clean tokens but use the text
                        cleaned_final = re.sub(pattern, '', final_response, flags=re.DOTALL).strip()
                        cleaned_final = re.sub(r'<\|tool_call[^|]*\|>', '', cleaned_final).strip()
                        assistant_text = cleaned_final
                else:
                    assistant_text = final_response
            else:
                assistant_text = final_response
    else:
        # No tools needed, use response as-is
        assistant_text = response.get('content', '')
        
        # Check if tool calls are in content but weren't parsed (Kimi format issue)
        if assistant_text and "<|tool_calls_section_begin|>" in assistant_text:
            logger.warning("Tool call tokens found in content but tool_calls not parsed. Attempting to parse manually.")
            # Manual parsing (same logic as in model_client)
            tool_calls = []
            pattern = r'<\|tool_calls_section_begin\|>(.*?)<\|tool_calls_section_end\|>'
            match = re.search(pattern, assistant_text, re.DOTALL)
            if match:
                tool_calls_section = match.group(1)
                tool_call_pattern = r'<\|tool_call_begin\|>functions\.([^:]+):\d+<\|tool_call_argument_begin\|>(.*?)<\|tool_call_end\|>'
                tool_call_matches = re.finditer(tool_call_pattern, tool_calls_section, re.DOTALL)
                
                for idx, tool_match in enumerate(tool_call_matches):
                    function_name = tool_match.group(1)
                    arguments_str = tool_match.group(2).strip()
                    try:
                        arguments = json.loads(arguments_str)
                        tool_calls.append({
                            'id': f"call_{idx}_{function_name}",
                            'type': 'function',
                            'function': {
                                'name': function_name,
                                'arguments': json.dumps(arguments, ensure_ascii=False)
                            }
                        })
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse tool call arguments for {function_name}: {e}")
            
            if tool_calls:
                logger.info(f"Manually parsed {len(tool_calls)} tool calls from content")
                # Execute the tool calls
                for tool_call in tool_calls:
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])
                    
                    logger.info(f"Executing manually parsed tool: {tool_name} with args: {tool_args}")
                    
                    # Execute the tool
                    tool_result = await tool_executor.execute_tool(tool_name, tool_args)
                    
                    # Check if tool wants to close connection
                    if tool_result.get('action') == 'close_connection':
                        should_close_connection = True
                        assistant_text = tool_result.get('message', 'Goodbye!')
                        break
                    else:
                        # Add tool result to messages for LLM to process
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "content": json.dumps(tool_result, default=str, ensure_ascii=False)
                        }
                        llm_messages.append(tool_message)
                
                # Get final response from LLM with tool results
                if not should_close_connection:
                    final_response = await model_client.generate_chat(
                        messages=llm_messages,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    assistant_text = final_response
            else:
                logger.warning("Could not parse tool calls from content. Cleaning tokens and using content as-is.")
                # Clean tokens but use the text part
                cleaned_content = model_client._clean_content_from_tool_calls(assistant_text)
                assistant_text = cleaned_content if cleaned_content else "I apologize, but I encountered an error processing your request."
    
    # Safety check: Remove tool call tokens if they somehow made it through
    if assistant_text and "<|tool_calls_section_begin|>" in assistant_text:
        logger.warning("Tool call tokens detected in final assistant text. Cleaning them.")
        # Remove tool calls section
        pattern = r'<\|tool_calls_section_begin\|>.*?<\|tool_calls_section_end\|>'
        assistant_text = re.sub(pattern, '', assistant_text, flags=re.DOTALL).strip()
        # Also remove any remaining individual tokens
        assistant_text = re.sub(r'<\|tool_call[^|]*\|>', '', assistant_text).strip()
    
    # Get message order before adding assistant message
    session = session_manager.get_session(session_id)
    message_order = len(session.get("messages", [])) if session else 0
    
    # Add assistant response to history
    session_manager.add_message(session_id, "assistant", assistant_text)
    
    # Store assistant message in database (async, non-blocking)
    if client_id:
        store_conversation_history_background(
            session_id=session_id,
            client_id=client_id,
            role="assistant",
            content=assistant_text,
            message_order=message_order + 1,  # +1 because we just added the message
        )
    
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
        
        # Store session_info in database (async, non-blocking)
        # Extract connection metadata if available
        client_host = websocket.client.host if websocket.client else None
        client_port = websocket.client.port if websocket.client else None
        ip_address = client_host
        
        # Try to get user agent from headers if available
        user_agent = None
        if hasattr(websocket, 'headers'):
            user_agent = websocket.headers.get('user-agent')
        
        # Store session info on connect (background task, won't block)
        store_session_info_background(
            session_id=session_id,
            client_id=client_id,
            started_at=None,  # Will default to now
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
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
        
        # Finalize session in database (async, non-blocking)
        # This will update ended_at and last_activity_at
        if session_id:
            finalize_session_background(session_id)
        
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

