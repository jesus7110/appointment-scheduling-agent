import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';
import LoadingAnimation from './LoadingAnimation';

// Backend WebSocket URL
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [clientId, setClientId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const menuRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showMenu]);

  // Load clientId from localStorage on mount (but don't auto-connect)
  useEffect(() => {
    const storedClientId = localStorage.getItem('clientId');
    if (storedClientId) {
      setClientId(storedClientId);
    }
    
    // Cleanup on unmount
    return () => {
      disconnectWebSocket();
    };
  }, []);

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      // Build WebSocket URL with clientId (from localStorage or state)
      const storedClientId = localStorage.getItem('clientId') || clientId;
      const wsUrl = storedClientId 
        ? `${WS_BASE_URL}/ws?client_id=${storedClientId}`
        : `${WS_BASE_URL}/ws`;
      
      console.log('Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        handleWebSocketMessage(data);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsConnected(false);
        wsRef.current = null;
        // No auto-reconnect - user must manually reconnect
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);
    }
  };

  const disconnectWebSocket = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  const handleWebSocketMessage = (data) => {
    const { type } = data;

    switch (type) {
      case 'client_registered':
        // Server assigned us a clientId
        const newClientId = data.client_id;
        setClientId(newClientId);
        localStorage.setItem('clientId', newClientId);
        console.log('Client registered:', newClientId);
        break;

      case 'session_created':
      case 'session_resumed':
        // Session created or resumed
        setSessionId(data.session_id);
        console.log('Session:', data.session_id);
        break;

      case 'message':
        // Received message from bot
        setIsLoading(false);
        
        const botPayload = data.bot_message || {
          msg_type: 'text',
          data: { msg_body: 'No response' }
        };

        const botMessage = {
          id: messages.length + Date.now(),
          ...botPayload,
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        
        setMessages(prev => [...prev, botMessage]);
        break;

      case 'typing':
        setIsLoading(data.is_typing);
        break;

      case 'error':
        setIsLoading(false);
        console.error('Server error:', data.message);
        
        const errorMessage = {
          id: messages.length + Date.now(),
          msg_type: 'text',
          data: { msg_body: `Error: ${data.message}` },
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, errorMessage]);
        break;

      case 'inactivity_timeout':
        // User was disconnected due to inactivity
        setIsLoading(false);
        console.log('Disconnected due to inactivity');
        
        const inactivityMessage = {
          id: messages.length + Date.now(),
          msg_type: 'text',
          data: { msg_body: '⚠️ You have been disconnected due to inactivity. Click the menu to reconnect.' },
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prev => [...prev, inactivityMessage]);
        
        // Immediately update connection status (don't wait for onclose)
        setIsConnected(false);
        
        // Close the WebSocket from client side as well
        if (wsRef.current) {
          wsRef.current.close();
          wsRef.current = null;
        }
        break;

      case 'pong':
        // Keep-alive response
        break;

      default:
        console.warn('Unknown message type:', type);
    }
  };

  const sendMessage = (content) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    try {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content: content
      }));
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleSend = () => {
    if (inputValue.trim() && !isLoading && isConnected) {
      const userMessage = {
        id: messages.length + Date.now(),
        text: inputValue,
        sender: 'user',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, userMessage]);
      sendMessage(inputValue);
      setInputValue('');
      setIsLoading(true);
    }
  };

  const handleActionClick = (messageId, actionKey, actionValue) => {
    // Disable all buttons for this specific message
    setMessages(prev => prev.map(msg => 
      msg.id === messageId && msg.msg_type === 'action1'
        ? { ...msg, actionsDisabled: true, selectedAction: actionKey }
        : msg
    ));

    // Send action selection as user message
    const userMessage = {
      id: messages.length + Date.now(),
      text: actionKey,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isAction: true,
      actionValue: actionValue
    };
    
    setMessages(prev => [...prev, userMessage]);
    sendMessage(actionKey);
    setIsLoading(true);
  };

  const handleRestart = () => {
    // Disconnect current WebSocket if connected
    if (isConnected) {
      disconnectWebSocket();
    }
    
    // Clear messages and state
    setMessages([]);
    setSessionId(null);
    setInputValue('');
    setIsLoading(false);
    setShowMenu(false);
    
    // Connect/Reconnect (will create new session)
    setTimeout(() => connectWebSocket(), 300);
  };

  const handleDisconnect = () => {
    disconnectWebSocket();
    setShowMenu(false);
  };

  const handleConnect = () => {
    connectWebSocket();
    setShowMenu(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="phone-container">
      {/* Phone Frame */}
      <div className="phone-frame">
        {/* Phone Notch */}
        <div className="phone-notch"></div>
        
        {/* Status Bar */}
        <div className="status-bar">
          <div className="status-left">
            <span className="status-time">9:41</span>
          </div>
          <div className="status-right">
            <span className="signal-bars">
              <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                <g fill="#ffffff">
                  <path d="m 9 4 c -0.554688 0 -1 0.445312 -1 1 v 9 c 0 0.554688 0.445312 1 1 1 h 1 c 0.554688 0 1 -0.445312 1 -1 v -9 c 0 -0.554688 -0.445312 -1 -1 -1 z m -4 3 c -0.554688 0 -1 0.445312 -1 1 v 6 c 0 0.554688 0.445312 1 1 1 h 1 c 0.554688 0 1 -0.445312 1 -1 v -6 c 0 -0.554688 -0.445312 -1 -1 -1 z m -4 3 c -0.554688 0 -1 0.445312 -1 1 v 3 c 0 0.554688 0.445312 1 1 1 h 1 c 0.554688 0 1 -0.445312 1 -1 v -3 c 0 -0.554688 -0.445312 -1 -1 -1 z m 0 0"></path>
                  <path d="m 13 1 c -0.554688 0 -1 0.445312 -1 1 v 12 c 0 0.554688 0.445312 1 1 1 h 1 c 0.554688 0 1 -0.445312 1 -1 v -12 c 0 -0.554688 -0.445312 -1 -1 -1 z m 0 0" fillOpacity="0.34902"></path>
                </g>
              </svg>
            </span>
            <span className="battery">
              <svg fill="#ffffff" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" width="18" height="18">
                <path d="m3.12 17.6c-1.723 0-3.12-1.397-3.12-3.12v-5.76c0-1.723 1.397-3.12 3.12-3.12h16.016c1.723 0 3.12 1.397 3.12 3.12v5.76c0 1.723-1.397 3.12-3.12 3.12zm-2.012-8.88v5.76c0 1.11.9 2.01 2.01 2.01h.002 16.016c1.109-.002 2.006-.902 2.006-2.01v-5.76c-.001-1.109-.9-2.008-2.009-2.01h-16.014-.001c-1.11 0-2.01.9-2.011 2.01zm2.678 6.4c-.724 0-1.31-.587-1.31-1.311v-4.423c0-.724.587-1.311 1.31-1.311h6.03c.724 0 1.31.587 1.31 1.31v4.428c-.001.724-.587 1.31-1.31 1.311zm18.871-5.41c.789.28 1.344 1.02 1.344 1.889s-.555 1.609-1.33 1.885l-.014.004z"></path>
              </svg>
            </span>
          </div>
        </div>

        {/* Chat Header */}
        <div className="chat-header">
          <div className="header-left">
            <button className="back-button">
              <svg fill="#ef6a36" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                <g id="SVGRepo_bgCarrier" strokeWidth="0"></g>
                <g id="SVGRepo_tracerCarrier" strokeLinecap="round" strokeLinejoin="round"></g>
                <g id="SVGRepo_iconCarrier">
                  <title>ionicons-v5-n</title>
                  <polygon points="351.9 256 460 193.6 412 110.4 304 172.8 304 48 208 48 208 172.8 100 110.4 52 193.6 160.1 256 52 318.4 100 401.6 208 339.2 208 464 304 464 304 339.2 412 401.6 460 318.4 351.9 256"></polygon>
                </g>
              </svg>
            </button>
            <div className="header-info">
              <h2>Appointment Assistant</h2>
              <span className={`status-text ${isConnected ? 'status-online' : 'status-offline'}`}>
                {isConnected ? 'Online' : 'Disconnected'}
              </span>
            </div>
          </div>
          <div className="menu-wrapper" ref={menuRef}>
            <button className="menu-button" onClick={() => setShowMenu(!showMenu)}>⋮</button>
            {showMenu && (
              <div className="dropdown-menu">
                <button className="dropdown-item" onClick={handleRestart}>
                  {isConnected ? 'Restart' : 'Connect'}
                </button>
                {isConnected && (
                  <button className="dropdown-item dropdown-item-disconnect" onClick={handleDisconnect}>
                    Disconnect
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Messages Container */}
        <div className="messages-container" ref={messagesContainerRef}>
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'message-user' : 'message-bot'}`}
            >
              <div className="message-bubble">
                {message.sender === 'user' ? (
                  // User messages (simple text)
                  <>
                    <p className="message-text">{message.text}</p>
                    <span className="message-time">{message.timestamp}</span>
                  </>
                ) : (
                  // Bot messages (structured: text or action1)
                  <>
                    {message.msg_type === 'text' ? (
                      // Simple text message
                      <>
                        <p className="message-text">{message.data.msg_body}</p>
                        <span className="message-time">{message.timestamp}</span>
                      </>
                    ) : message.msg_type === 'action1' ? (
                      // Action message with selectable buttons
                      <>
                        <p className="message-text">{message.data.msg_body}</p>
                        <div className="action-buttons">
                          {message.data.action && message.data.action.map((action, index) => (
                            <button
                              key={index}
                              className={`action-button ${message.actionsDisabled ? 'action-button-disabled' : ''} ${message.selectedAction === action.key ? 'action-button-selected' : ''}`}
                              onClick={() => !message.actionsDisabled && handleActionClick(message.id, action.key, action.value)}
                              disabled={message.actionsDisabled}
                            >
                              {action.key}
                            </button>
                          ))}
                        </div>
                        <span className="message-time">{message.timestamp}</span>
                      </>
                    ) : (
                      // Fallback for unknown message types
                      <>
                        <p className="message-text">{message.text || JSON.stringify(message.data)}</p>
                        <span className="message-time">{message.timestamp}</span>
                      </>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message message-bot loading-message">
              <LoadingAnimation />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-wrapper">
            <input
              type="text"
              className="message-input"
              placeholder={isLoading ? "Waiting for response..." : isConnected ? "Type your message..." : "Click menu to connect..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading || !isConnected}
            />
            <button className="send-button" onClick={handleSend} disabled={isLoading || !isConnected}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </div>

        {/* Home Indicator (for iPhone-style phones) */}
        <div className="home-indicator"></div>
      </div>
    </div>
  );
};

export default ChatInterface;
