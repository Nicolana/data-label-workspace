from fastapi import APIRouter
from app.db.repositories.conversation import ChatConversationRepository
from app.models.conversation import ChatConversation
from app.services.openai import OpenAIService
from app.models.response import ApiResponse, success
from app.core.exceptions import NotFoundException
from typing import List

router = APIRouter()
openai_service = OpenAIService()

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
