from fastapi import APIRouter, HTTPException
from typing import List
from app.models.conversation import Conversation, Message, ChatConversation, ChatMessage
from app.db.repositories.conversation import ConversationRepository, ChatConversationRepository
from app.services.openai import OpenAIService

router = APIRouter()
openai_service = OpenAIService()

@router.post("/conversations", response_model=Conversation)
async def create_conversation(conversation: Conversation):
    return ConversationRepository.create(conversation.title, conversation.messages)

@router.get("/conversations", response_model=List[Conversation])
async def list_conversations():
    return ConversationRepository.list()

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: int):
    conversation = ConversationRepository.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation

@router.post("/conversations/{conversation_id}/copy")
async def copy_conversation(conversation_id: int):
    conversation = ConversationRepository.copy(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    if not ConversationRepository.delete(conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"message": "对话删除成功"}

@router.post("/chat-conversations", response_model=ChatConversation)
async def create_chat_conversation(conversation: ChatConversation):
    return ChatConversationRepository.create(conversation.title)

@router.get("/chat-conversations", response_model=List[ChatConversation])
async def list_chat_conversations():
    return ChatConversationRepository.list()

@router.get("/chat-conversations/{conversation_id}", response_model=ChatConversation)
async def get_chat_conversation(conversation_id: int):
    conversation = ChatConversationRepository.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation

@router.delete("/chat-conversations/{conversation_id}")
async def delete_chat_conversation(conversation_id: int):
    if not ChatConversationRepository.delete(conversation_id):
        raise HTTPException(status_code=404, detail="对话不存在")
    return {"message": "对话删除成功"}

@router.put("/chat-conversations/{conversation_id}/title", response_model=ChatConversation)
async def update_chat_conversation_title(conversation_id: int, title: str):
    conversation = ChatConversationRepository.update_title(conversation_id, title)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    return conversation 