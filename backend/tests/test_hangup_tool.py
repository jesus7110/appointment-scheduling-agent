"""
Test the hang up / end conversation tool.

This tests if the LLM can detect when a user wants to end the conversation
and call the appropriate tool.
"""

import asyncio
import os
from dotenv import load_dotenv
from agent.model_client import ModelClient, reset_model_client
from tools.tool_definitions import get_test_tools
from tools.tool_executor import get_tool_executor
import json

load_dotenv()

async def test_hangup_detection():
    """Test if LLM detects hang up intent and calls the tool."""
    
    print("=" * 70)
    print("HANG UP TOOL TEST")
    print("=" * 70)
    print()
    
    # Reset and get client
    reset_model_client()
    client = ModelClient()
    executor = get_tool_executor()
    
    print(f"Provider: {client.provider}")
    print(f"Model: {client.model}")
    print()
    
    # Get tools
    tools = get_test_tools()
    print(f"Available tools: {[t['function']['name'] for t in tools]}")
    print()
    
    # Test cases
    test_cases = [
        "I want to hang up now",
        "Goodbye, I'm done",
        "Thanks, I need to go",
        "End this conversation please",
        "Bye bye",
        "Let me disconnect",
        "I'm leaving now",
        "Can I book an appointment?"  # This should NOT trigger hangup
    ]
    
    for i, user_message in enumerate(test_cases, 1):
        print("=" * 70)
        print(f"Test Case #{i}: '{user_message}'")
        print("-" * 70)
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # Call LLM with tools
            response = await client.generate_chat_with_tools(
                messages=messages,
                tools=tools,
                temperature=0.7,
                max_tokens=200
            )
            
            # Check if tool was called
            if 'tool_calls' in response and response['tool_calls']:
                print("✅ LLM CALLED A TOOL!")
                
                for tool_call in response['tool_calls']:
                    tool_name = tool_call['function']['name']
                    tool_args = json.loads(tool_call['function']['arguments'])
                    
                    print(f"   Tool: {tool_name}")
                    print(f"   Arguments: {tool_args}")
                    
                    # Execute the tool
                    result = executor.execute_tool(tool_name, tool_args)
                    print(f"   Result: {result}")
                    
                    if result.get('action') == 'close_connection':
                        print()
                        print(f"   🔌 CONNECTION WOULD CLOSE")
                        print(f"   💬 Goodbye message: \"{result.get('message')}\"")
            else:
                print("❌ No tool called")
                print(f"   LLM response: {response.get('content', '')[:100]}...")
            
            print()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()
    
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_hangup_detection())

