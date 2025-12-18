"""
Test to check what Groq models are available and test tool calling with actual Groq models.
"""

import asyncio
import os
from dotenv import load_dotenv
from litellm import completion
import json

load_dotenv()

async def test_groq_models():
    """Test with actual Groq models."""
    
    print("=" * 70)
    print("TESTING GROQ MODELS")
    print("=" * 70)
    
    # Get API key
    groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
    
    if not groq_api_key:
        print("❌ No GROQ_API_KEY or LLM_API_KEY found in .env")
        return
    
    print(f"✅ API Key found: {groq_api_key[:10]}...")
    print()
    
    # Actual Groq models that exist
    groq_models = [
        "groq/llama-3.3-70b-versatile",
        "groq/llama-3.1-70b-versatile", 
        "groq/llama-3.1-8b-instant",
        "groq/mixtral-8x7b-32768",
        "groq/gemma2-9b-it",
    ]
    
    print("Available Groq Models:")
    for model in groq_models:
        print(f"  - {model}")
    print()
    print("=" * 70)
    print()
    
    # Test the model from .env first
    current_model = os.getenv("LLM_MODEL")
    print(f"Testing your current model: {current_model}")
    print("-" * 70)
    
    # Try with groq/ prefix
    if not current_model.startswith("groq/"):
        test_model = f"groq/{current_model}"
    else:
        test_model = current_model
    
    success = await test_model_tool_calling(test_model, groq_api_key)
    
    if not success:
        print()
        print("Your current model didn't work. Let's try a known Groq model...")
        print()
        
        # Try llama-3.3-70b-versatile
        print("=" * 70)
        print("Testing: groq/llama-3.3-70b-versatile")
        print("-" * 70)
        await test_model_tool_calling("groq/llama-3.3-70b-versatile", groq_api_key)


async def test_model_tool_calling(model: str, api_key: str) -> bool:
    """Test tool calling for a specific model."""
    
    # Set API key
    os.environ["GROQ_API_KEY"] = api_key
    
    # Simple tool
    tools = [{
        "type": "function",
        "function": {
            "name": "log_message",
            "description": "Log a message to console",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        }
    }]
    
    try:
        # Test 1: Basic call
        print("Test 1: Basic connectivity...")
        response = completion(
            model=model,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=20
        )
        print(f"✅ Basic call works")
        print(f"   Response: {response.choices[0].message.content}")
        print()
        
        # Test 2: Tool calling
        print("Test 2: Tool calling...")
        response = completion(
            model=model,
            messages=[{"role": "user", "content": "Log the message 'Hello from LLM'"}],
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"🎉 ✅ TOOL CALLING WORKS!")
            print()
            for tool_call in message.tool_calls:
                print(f"  Tool: {tool_call.function.name}")
                print(f"  Args: {tool_call.function.arguments}")
            print()
            print("=" * 70)
            print(f"✅ SUCCESS! Use this in your .env:")
            print("=" * 70)
            print(f"LLM_MODEL={model}")
            print("=" * 70)
            return True
        else:
            print(f"❌ Tool calling not supported")
            print(f"   Got text response: {message.content[:100]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)[:200]}")
        return False


if __name__ == "__main__":
    asyncio.run(test_groq_models())

