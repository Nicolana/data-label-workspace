from typing import List
from git import Optional
from pydantic import BaseModel
from app.models.conversation import Message



class CreateChatRequest(BaseModel):
    title: Optional[str] = None
    messages: List[List[Message]]


class UpdateChatRequest(BaseModel):
    title: str
    messages: List[List[Message]]

class DeleteChatRequest(BaseModel):
    id: int

class GetChatRequest(BaseModel):
    id: int

class CopyChatRequest(BaseModel):
    id: int

