# Inactivity Timeout Feature

## Overview
Users are automatically disconnected after **1 minute (60 seconds)** of inactivity to free up server resources.

## How It Works

### Backend (websocket.py)
- Uses `asyncio.wait_for()` with 60-second timeout on message reception
- When timeout occurs:
  1. Sends `inactivity_timeout` message to frontend
  2. Waits 0.1s for message delivery
  3. Explicitly closes the WebSocket with code 1000
  4. Logs the disconnection
  5. Session data remains in memory (not deleted)

### Frontend (ChatInterface.jsx)
- Receives `inactivity_timeout` message
- Displays warning message: "⚠️ You have been disconnected due to inactivity..."
- **Immediately** sets connection status to "Disconnected"
- Closes WebSocket from client side to prevent race conditions
- Disables message input (greyed out)
- User can reconnect via the menu button

## Flow Diagram

```
User sends message ─────► Backend resets timer (60s)
                          │
                          │ (User inactive for 60s)
                          │
                          ▼
                    Timeout triggered
                          │
                          ├─► Send "inactivity_timeout" message
                          ├─► Close WebSocket
                          └─► Frontend shows warning message
                                    │
                                    ▼
                              Status: "Disconnected"
                                    │
                                    ▼
                          User clicks menu → Reconnect
```

## Testing

1. **Start both frontend and backend**
2. **Connect and send a message**
3. **Wait 60 seconds without sending any message**
4. **Observe:**
   - Console log: "Inactivity timeout for session {session_id}"
   - Frontend shows: "⚠️ You have been disconnected due to inactivity..."
   - Status changes to "Disconnected"
5. **Click menu → Connect/Restart to reconnect**

## Configuration

To change the timeout duration, modify this line in `backend/api/websocket.py`:

```python
INACTIVITY_TIMEOUT = 60  # Change to desired seconds
```

## Notes

- Ping messages from frontend also reset the timer (if implemented)
- Session history is preserved even after disconnection
- The timeout is per WebSocket connection, not per user
- Multiple tabs = multiple connections = each has its own timer

## Bug Fixes Applied

### Issue: Connection status not updating immediately
**Problem:** After timeout, the UI still showed "Online" and accepted user input for a brief moment.

**Root Cause:** 
- Backend was breaking from loop without explicitly closing WebSocket
- Frontend waited for `onclose` event, creating a race condition
- User could send messages during this gap

**Solution:**
1. **Backend:** Explicitly call `websocket.close(code=1000)` after sending timeout message
2. **Frontend:** Immediately set `isConnected = false` when receiving `inactivity_timeout` message
3. **Frontend:** Close WebSocket from client side as well to prevent race conditions

**Result:** UI instantly reflects disconnected state, input is disabled, status shows "Disconnected"

