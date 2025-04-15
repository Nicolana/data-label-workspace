from typing import List, Optional
from pydantic import BaseModel
from app.models.conversation import Message, Conversation, ChatConversation, ChatMessage

class ConversationResponse(BaseModel):
    id: int
    messages: List[Message]
    token_count: Optional[int] = None
    message_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ChatConversationResponse(BaseModel):
    id: int
    title: str
    message_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
