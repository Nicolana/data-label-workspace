from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from .base import BaseDBModel

class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseDBModel):
    title: str
    messages: List[Message]
    token_count: Optional[int] = None
    message_count: Optional[int] = None

class ChatConversation(BaseDBModel):
    title: str
    message_count: Optional[int] = None

class ChatMessage(BaseDBModel):
    conversation_id: int
    role: str
    content: str 