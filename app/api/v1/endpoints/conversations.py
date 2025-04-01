from fastapi import APIRouter, HTTPException
from typing import List
from app.core.exceptions import NotFoundException
from app.models.conversation import Conversation, Message, ChatConversation, ChatMessage
from app.db.repositories.conversation import ConversationRepository, ChatConversationRepository
from app.models.response import ApiResponse, success
from app.services.openai import OpenAIService

router = APIRouter()
openai_service = OpenAIService()

@router.post("/conversations", response_model=ApiResponse[Conversation])
async def create_conversation(conversation: Conversation):
    return success(data=ConversationRepository.create(conversation.title, conversation.messages))

@router.get("/conversations", response_model=ApiResponse[List[Conversation]])
async def list_conversations():
    return success(data=ConversationRepository.list())

@router.get("/conversations/{conversation_id}", response_model=ApiResponse[Conversation])
async def get_conversation(conversation_id: int):
    conversation = ConversationRepository.get(conversation_id)
    if not conversation:
        raise NotFoundException(message="对话不存在")
    return success(data=conversation)

@router.post("/conversations/{conversation_id}/copy")
async def copy_conversation(conversation_id: int):
    conversation = ConversationRepository.copy(conversation_id)
    if not conversation:
        return NotFoundException(message="对话不存在")
    return success(data=conversation)

@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(conversation_id: int, conversation: Conversation):
    updated_conversation = ConversationRepository.update(conversation_id, conversation)
    if not updated_conversation:
        raise NotFoundException(message="对话不存在")
    return success(data=updated_conversation)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    if not ConversationRepository.delete(conversation_id):
        raise NotFoundException(message="对话不存在")
    return success(message="对话删除成功")

@router.post("/chat-conversations", response_model=ApiResponse[ChatConversation])
async def create_chat_conversation(conversation: ChatConversation):
    return success(data=ChatConversationRepository.create(conversation.title))

@router.get("/chat-conversations", response_model=ApiResponse[List[ChatConversation]])
async def list_chat_conversations():
    return success(data=ChatConversationRepository.list())

@router.get("/chat-conversations/{conversation_id}", response_model=ApiResponse[ChatConversation])
async def get_chat_conversation(conversation_id: int):
    conversation = ChatConversationRepository.get(conversation_id)
    if not conversation:
        raise NotFoundException(message="对话不存在")
    return success(data=conversation)

@router.delete("/chat-conversations/{conversation_id}")
async def delete_chat_conversation(conversation_id: int):
    if not ChatConversationRepository.delete(conversation_id):
        raise NotFoundException(message="对话不存在")
    return success(message="对话删除成功")

@router.put("/chat-conversations/{conversation_id}/title", response_model=ApiResponse[ChatConversation])
async def update_chat_conversation_title(conversation_id: int, title: str):
    conversation = ChatConversationRepository.update_title(conversation_id, title)
    if not conversation:
        raise NotFoundException(message="对话不存在")
    return success(data=conversation)
