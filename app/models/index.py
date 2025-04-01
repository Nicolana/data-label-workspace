from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from .base import BaseDBModel
from enum import Enum

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

class ChunkingStrategy(str, Enum):
    """文档切片策略"""
    PARAGRAPH = "paragraph"  # 按段落切分
    FIXED_SIZE = "fixed_size"  # 按固定字符数切分
    SENTENCE = "sentence"  # 按句子切分
    NO_CHUNKING = "no_chunking"  # 不切分，整个文档作为一个块

class ChunkingConfig(BaseModel):
    """文档切片配置"""
    strategy: ChunkingStrategy = Field(ChunkingStrategy.PARAGRAPH, description="切片策略")
    chunk_size: Optional[int] = Field(500, description="当策略为fixed_size时的块大小(字符数)")
    chunk_overlap: Optional[int] = Field(50, description="块之间的重叠字符数")
    separator: Optional[str] = Field(None, description="自定义分隔符")

class FileUploadRequest(BaseModel):
    """文件上传请求"""
    index_id: int
    chunking_config: ChunkingConfig
    metadata: Optional[Dict[str, Any]] = Field(None, description="要添加到所有文档的元数据")

class ProcessedFileInfo(BaseModel):
    """处理后的文件信息"""
    filename: str
    chunk_count: int
    total_characters: int