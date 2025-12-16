# Data schemas
from pydantic import BaseModel
from typing import List, Dict, Optional, Union

class TextMessageData(BaseModel):
    msg_body: str

class ActionMessageData(BaseModel):
    msg_body: str
    action: List[Dict[str, str]]  # List of key-value pairs

class MessageResponse(BaseModel):
    msg_type: str  # "text" or "action1"
    data: Union[TextMessageData, ActionMessageData]

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
