// Mock API to simulate backend responses
// Returns structured messages alternating between "text" and "action1" types

let messageCounter = 0;

const mockResponses = {
  text: [
    {
      msg_type: "text",
      data: {
        msg_body: "Hello! I'm here to help you schedule an appointment. How can I assist you today?"
      }
    },
    {
      msg_type: "text",
      data: {
        msg_body: "Thank you for your message. I'm processing your request..."
      }
    },
    {
      msg_type: "text",
      data: {
        msg_body: "I understand you'd like to schedule an appointment. Let me check the available time slots for you."
      }
    },
    {
      msg_type: "text",
      data: {
        msg_body: "Great! I've found some available appointments. Please select a time slot that works for you."
      }
    },
    {
      msg_type: "text",
      data: {
        msg_body: "Perfect! Your appointment has been scheduled. You'll receive a confirmation shortly."
      }
    }
  ],
  action1: [
    {
      msg_type: "action1",
      data: {
        msg_body: "Here are the available time slots for today:",
        action: [
          { key: "9:00 AM", value: "2024-01-15T09:00:00" },
          { key: "10:30 AM", value: "2024-01-15T10:30:00" },
          { key: "2:00 PM", value: "2024-01-15T14:00:00" },
          { key: "3:30 PM", value: "2024-01-15T15:30:00" }
        ]
      }
    },
    {
      msg_type: "action1",
      data: {
        msg_body: "Please select your preferred appointment type:",
        action: [
          { key: "General Consultation", value: "general" },
          { key: "Follow-up Visit", value: "followup" },
          { key: "Emergency", value: "emergency" }
        ]
      }
    },
    {
      msg_type: "action1",
      data: {
        msg_body: "Available slots for tomorrow:",
        action: [
          { key: "8:00 AM", value: "2024-01-16T08:00:00" },
          { key: "11:00 AM", value: "2024-01-16T11:00:00" },
          { key: "1:00 PM", value: "2024-01-16T13:00:00" },
          { key: "4:00 PM", value: "2024-01-16T16:00:00" }
        ]
      }
    },
    {
      msg_type: "action1",
      data: {
        msg_body: "Choose a doctor:",
        action: [
          { key: "Dr. Smith", value: "doctor_smith" },
          { key: "Dr. Johnson", value: "doctor_johnson" },
          { key: "Dr. Williams", value: "doctor_williams" }
        ]
      }
    }
  ]
};

/**
 * Simulates an API call to get a bot response
 * Alternates between "text" and "action1" message types
 * @param {string} userMessage - The user's message (optional, for future use)
 * @returns {Promise<Object>} - A promise that resolves to a structured message object
 */
export const getBotResponse = async (userMessage = "") => {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 1500));

  // Alternate between text and action1 messages
  const isTextMessage = messageCounter % 2 === 0;
  
  if (isTextMessage) {
    // Get a text message (cycling through available text messages)
    const textIndex = Math.floor((messageCounter / 2) % mockResponses.text.length);
    messageCounter++;
    return mockResponses.text[textIndex];
  } else {
    // Get an action1 message (cycling through available action1 messages)
    const actionIndex = Math.floor((messageCounter / 2) % mockResponses.action1.length);
    messageCounter++;
    return mockResponses.action1[actionIndex];
  }
};

/**
 * Reset the message counter (useful for restarting the conversation)
 */
export const resetMockAPI = () => {
  messageCounter = 0;
};

