#!/usr/bin/env python3
"""
Quick test script to verify Groq API configuration.
Run this to ensure your Groq setup is working correctly.

Usage:
    From project root: python backend/tests/test_groq.py
    From backend/: python tests/test_groq.py
    From backend/tests/: python test_groq.py

Note: Make sure .env file is in the backend/ directory
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add parent directory to path to import from agent module
# This script is in backend/tests/, so we need to go up one level to backend/
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from agent.model_client import ModelClient


async def test_groq_connection():
    """Test the Groq API connection and model response."""
    
    print("=" * 60)
    print("Testing Groq API Configuration")
    print("=" * 60)
    print()
    
    # Load environment variables from backend directory
    # .env is in backend/ (one level up from tests/)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(backend_dir, '.env')
    load_dotenv(dotenv_path=env_path)
    
    # Check if required env vars are set
    provider = os.getenv("LLM_PROVIDER", "Not set")
    model = os.getenv("LLM_MODEL", "Not set")
    api_key = os.getenv("LLM_API_KEY", "Not set")
    
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"API Key: {'✅ Set' if api_key != 'Not set' and api_key else '❌ Not set'}")
    print()
    
    if provider.lower() != "groq":
        print("⚠️  Warning: LLM_PROVIDER is not set to 'groq'")
        print("   Current provider:", provider)
        print("   To use Groq, set LLM_PROVIDER=groq in your .env file")
        print()
    
    if not api_key or api_key == "Not set":
        print("❌ Error: LLM_API_KEY is not set")
        print()
        print("Please set your Groq API key in .env file:")
        print("  LLM_API_KEY=gsk_your_api_key_here")
        print()
        print("Get your API key from: https://console.groq.com/keys")
        sys.exit(1)
    
    try:
        # Initialize the model client
        print("Initializing ModelClient...")
        client = ModelClient()
        
        # Get model info
        info = client.get_model_info()
        print(f"✅ Client initialized successfully")
        print(f"   Using model: {info['model']}")
        print(f"   Temperature: {info['temperature']}")
        print(f"   Max tokens: {info['max_tokens']}")
        print()
        
        # Test a simple message
        print("Sending test message to Groq API...")
        print("-" * 60)
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful medical appointment scheduling assistant."
            },
            {
                "role": "user",
                "content": "Say 'Hello! I'm ready to help with appointments.' in one sentence."
            }
        ]
        
        response = await client.generate_chat(messages, max_tokens=100)
        
        print("Response received:")
        print(f"  {response}")
        print("-" * 60)
        print()
        
        if response:
            print("✅ Success! Groq API is working correctly.")
            print()
            print("You can now run your application:")
            print("  cd backend")
            print("  uvicorn main:app --reload")
        else:
            print("❌ Error: Received empty response")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Verify your API key is correct")
        print("2. Check your internet connection")
        print("3. Visit https://console.groq.com to check service status")
        print("4. Make sure litellm is installed: pip install litellm")
        sys.exit(1)
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_groq_connection())

