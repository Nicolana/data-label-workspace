from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from .base import BaseDBModel

class IndexCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Index(BaseDBModel):
    name: str
    description: Optional[str]
    document_count: int

class DocumentCreate(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class Document(BaseDBModel):
    index_id: int
    content: str
    metadata: Optional[Dict[str, Any]]
    similarity: Optional[float] = None 

class DocumentRecallRequest(BaseModel):
    index_id: int
    query: str
    top_k: Optional[int] = 5