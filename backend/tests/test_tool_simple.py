"""
Simple tool calling test - just logs to console when called.
This will clearly show if your LLM supports tool calling.

Uses LLM_PROVIDER, LLM_MODEL, and LLM_API_KEY from .env file.
"""

import asyncio
import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

async def test_simple_tool():
    """Test with a simple logging tool."""
    
    print("=" * 70)
    print("SIMPLE TOOL CALLING TEST")
    print("=" * 70)
    
    # Get configuration from environment
    provider = os.getenv("LLM_PROVIDER", "openai")
    raw_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    api_key = os.getenv("LLM_API_KEY")
    
    print(f"Provider: {provider}")
    print(f"Model (raw): {raw_model}")
    print(f"API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    if not api_key:
        print("❌ ERROR: LLM_API_KEY not found in .env file")
        print("Please set LLM_API_KEY in your .env file")
        return
    
    # Normalize model name based on provider (like ModelClient does)
    if provider.lower() in ["google", "gemini"]:
        if not raw_model.startswith("gemini/"):
            model = f"gemini/{raw_model}"
        else:
            model = raw_model
        os.environ["GOOGLE_API_KEY"] = api_key
    elif provider.lower() == "openai":
        model = raw_model
        os.environ["OPENAI_API_KEY"] = api_key
    elif provider.lower() == "anthropic":
        model = raw_model
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif provider.lower() == "groq":
        if not raw_model.startswith("groq/"):
            model = f"groq/{raw_model}"
        else:
            model = raw_model
        os.environ["GROQ_API_KEY"] = api_key
    else:
        model = raw_model
        os.environ["LITELLM_API_KEY"] = api_key
    
    print(f"Model (formatted): {model}")
    print()
    
    # Define a simple test tool
    tools = [{
        "type": "function",
        "function": {
            "name": "log_message",
            "description": "Log a message to the console. Call this when the user asks you to log something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to log"
                    }
                },
                "required": ["message"]
            }
        }
    }]
    
    # Test query that should trigger the tool
    user_query = "Please log the message 'Hello from LLM' to the console"
    
    print(f"User Query: '{user_query}'")
    print()
    print("-" * 70)
    print()
    
    try:
        # Call LLM with the tool
        response = completion(
            model=model,
            messages=[{"role": "user", "content": user_query}],
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        # Check if tool was called
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print("🎉 SUCCESS! LLM CALLED THE TOOL!")
            print()
            
            for i, tool_call in enumerate(message.tool_calls, 1):
                print(f"Tool Call #{i}:")
                print(f"  ID: {tool_call.id}")
                print(f"  Function: {tool_call.function.name}")
                print(f"  Arguments: {tool_call.function.arguments}")
                print()
            
            # Simulate executing the tool
            import json
            for tool_call in message.tool_calls:
                if tool_call.function.name == "log_message":
                    args = json.loads(tool_call.function.arguments)
                    print("=" * 70)
                    print("🔧 EXECUTING TOOL: log_message")
                    print("=" * 70)
                    print(f"📝 LOGGED MESSAGE: {args.get('message')}")
                    print("=" * 70)
            
            print()
            print("✅ CONCLUSION: Native tool calling IS SUPPORTED")
            print("   You can use the tool calling implementation!")
            
        else:
            print("❌ LLM DID NOT CALL THE TOOL")
            print()
            print("Instead, it responded with text:")
            print("-" * 70)
            print(message.content)
            print("-" * 70)
            print()
            print("✅ CONCLUSION: Native tool calling NOT SUPPORTED")
            print("   Use ReAct prompting pattern instead")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print()
        
        # Check error type
        error_str = str(e).lower()
        if "tool" in error_str or "function" in error_str:
            print("DIAGNOSIS: This model doesn't support tools/functions")
        elif "not found" in error_str or "invalid" in error_str:
            print("DIAGNOSIS: Model identifier might be wrong")
        else:
            print("DIAGNOSIS: Unknown error - check your API key and model name")
        
        print()
        print("✅ CONCLUSION: Native tool calling NOT SUPPORTED")
        print("   Use ReAct prompting pattern instead")
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_simple_tool())