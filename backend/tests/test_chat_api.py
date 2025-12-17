"""
Simple test script for the chat API endpoint.

Make sure the server is running first:
    python backend/main.py

Then run this test:
    python backend/test_chat_api.py
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"


def test_health():
    """Test the health endpoint."""
    print("=" * 60)
    print("Test 1: Health Check")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_context():
    """Test the context endpoint."""
    print("\n" + "=" * 60)
    print("Test 2: Get Context")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/context")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"\nContext Data:")
        print(f"  Clinics: {data['data']['total_clinics']}")
        print(f"  Doctors: {data['data']['total_doctors']}")
        print(f"  Specialties: {len(data['data']['specialties'])}")
        print(f"  Cities: {', '.join(data['data']['cities'])}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chat():
    """Test the chat endpoint."""
    print("\n" + "=" * 60)
    print("Test 3: Chat Endpoint")
    print("=" * 60)
    
    # Test message
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Hello! I need to book an appointment with a cardiologist."
            }
        ],
        "session_id": "test-session-001"
    }
    
    try:
        print("\n📤 Sending message:")
        print(f"   User: {payload['messages'][0]['content']}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📥 Response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Assistant: {data['message']}")
            print(f"   Session ID: {data.get('session_id')}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_multi_turn_chat():
    """Test multi-turn conversation."""
    print("\n" + "=" * 60)
    print("Test 4: Multi-turn Conversation")
    print("=" * 60)
    
    # Simulate a conversation
    conversation = [
        {"role": "user", "content": "I'm looking for a pediatrician in Saket."},
    ]
    
    try:
        print("\n💬 Starting conversation...")
        
        # First message
        print(f"\n👤 User: {conversation[0]['content']}")
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"messages": conversation, "session_id": "test-session-002"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assistant_msg = data['message']
            print(f"🤖 Assistant: {assistant_msg[:200]}...")
            
            # Add to conversation history
            conversation.append({"role": "assistant", "content": assistant_msg})
            
            # Second message
            conversation.append({
                "role": "user",
                "content": "What are the consultation fees?"
            })
            
            print(f"\n👤 User: {conversation[-1]['content']}")
            
            response2 = requests.post(
                f"{BASE_URL}/api/chat",
                json={"messages": conversation, "session_id": "test-session-002"}
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"🤖 Assistant: {data2['message'][:200]}...")
                return True
            else:
                print(f"❌ Second message failed: {response2.text}")
                return False
        else:
            print(f"❌ First message failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n🧪 Testing Chat API Endpoint")
    print("Make sure the server is running on http://localhost:8100\n")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Context", test_context()))
    results.append(("Chat", test_chat()))
    results.append(("Multi-turn Chat", test_multi_turn_chat()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    exit(main())

