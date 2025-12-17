"""
Simple test script to verify model_client is working.

Run this script directly to test your LLM configuration:
    python backend/test_model_client.py

Make sure your .env file has:
    LLM_PROVIDER=google (or openai, anthropic, etc.)
    LLM_MODEL=gemini/gemini-2.0-flash (or your preferred model)
    LLM_API_KEY=your_api_key_here
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import
sys.path.insert(0, str(Path(__file__).parent))

from agent.model_client import ModelClient, get_model_client


async def test_basic_chat():
    """Test basic chat completion."""
    print("=" * 60)
    print("Testing Model Client - Basic Chat")
    print("=" * 60)
    
    try:
        # Get the model client
        client = get_model_client()
        
        # Display configuration
        info = client.get_model_info()
        print(f"\n📋 Configuration:")
        print(f"   Provider: {info['provider']}")
        print(f"   Model: {info['model']}")
        print(f"   Temperature: {info['temperature']}")
        print(f"   Max Tokens: {info['max_tokens']}")
        print(f"   API Key Set: {info['api_key_set']}")
        
        # Test message
        test_messages = [
            {"role": "user", "content": "Say 'Hello, I am working!' in exactly those words."}
        ]
        
        print(f"\n💬 Sending test message...")
        print(f"   Message: {test_messages[0]['content']}")
        
        # Generate response
        response = await client.generate_chat(test_messages)
        
        print(f"\n✅ Success! Response received:")
        print(f"   {response}")
        print("\n" + "=" * 60)
        return True
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Make sure your .env file has:")
        print("   LLM_PROVIDER=your_provider")
        print("   LLM_MODEL=your_model")
        print("   LLM_API_KEY=your_api_key")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


async def test_streaming():
    """Test streaming chat completion."""
    print("\n" + "=" * 60)
    print("Testing Model Client - Streaming")
    print("=" * 60)
    
    try:
        client = get_model_client()
        
        test_messages = [
            {"role": "user", "content": "Count from 1 to 5, one number per line."}
        ]
        
        print(f"\n💬 Sending streaming test message...")
        print(f"   Message: {test_messages[0]['content']}")
        print(f"\n📡 Streaming response:")
        print("   ", end="", flush=True)
        
        # Stream response
        full_response = ""
        async for chunk in client.generate_chat_stream(test_messages):
            print(chunk, end="", flush=True)
            full_response += chunk
        
        print(f"\n\n✅ Streaming completed!")
        print(f"   Full response length: {len(full_response)} characters")
        print("\n" + "=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Streaming Error: {e}")
        return False


async def test_custom_parameters():
    """Test with custom temperature and max_tokens."""
    print("\n" + "=" * 60)
    print("Testing Model Client - Custom Parameters")
    print("=" * 60)
    
    try:
        client = get_model_client()
        
        test_messages = [
            {"role": "user", "content": "Say 'test' and nothing else."}
        ]
        
        print(f"\n💬 Testing with custom parameters...")
        print(f"   Temperature: 0.1 (lower = more deterministic)")
        print(f"   Max Tokens: 50")
        
        response = await client.generate_chat(
            test_messages,
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"\n✅ Success! Response:")
        print(f"   {response}")
        print("\n" + "=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n🚀 Starting Model Client Tests\n")
    
    results = []
    
    # Test 1: Basic chat
    results.append(await test_basic_chat())
    
    # Test 2: Streaming (optional, comment out if you want to skip)
    # results.append(await test_streaming())
    
    # Test 3: Custom parameters
    results.append(await test_custom_parameters())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! Model client is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

