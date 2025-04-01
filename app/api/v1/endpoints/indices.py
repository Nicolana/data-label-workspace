from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import json
import os
import shutil
import tempfile
from datetime import datetime
from pydantic import parse_obj_as, BaseModel

from app.core.exceptions import NotFoundException
from app.models.index import DocumentRecallRequest, Index, IndexCreate, Document, DocumentCreate, FileUploadRequest, ChunkingConfig, ProcessedFileInfo
from app.models.response import ApiResponse, success
from app.db.repositories.index import IndexRepository, DocumentRepository
from app.services.embedding import EmbeddingService
from app.services.document_processor import DocumentProcessor

router = APIRouter()
embedding_service = EmbeddingService()

# 临时文件存储目录
TEMP_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "temp_uploads")
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# 代码仓库索引请求模型
class RepoIndexRequest(BaseModel):
    repo_path: str
    chunking_config: ChunkingConfig
    recursive: bool = True
    metadata: Optional[Dict[str, Any]] = None

# 代码仓库索引结果
class RepoIndexResult(BaseModel):
    total_files: int
    total_chunks: int
    total_characters: int
    processed_files: List[ProcessedFileInfo]

@router.post("/indices", response_model=ApiResponse[Index])
async def create_index(index: IndexCreate):
    return success(data=IndexRepository.create(index))

@router.get("/indices", response_model=ApiResponse[List[Index]])
async def list_indices():
    return success(data=IndexRepository.list())

@router.get("/indices/{index_id}", response_model=ApiResponse[Index])
async def get_index(index_id: int):
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    return success(data=index)

@router.delete("/indices/{index_id}")
async def delete_index(index_id: int):
    if not IndexRepository.delete(index_id):
        raise NotFoundException(message="索引不存在")
    return success(message="索引删除成功")

@router.post("/indices/{index_id}/documents", response_model=ApiResponse[Document])
async def add_document(index_id: int, document: DocumentCreate):
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    # 获取文档向量
    embedding = embedding_service.get_embedding(document.content)
    
    # 创建文档
    return success(data=DocumentRepository.create(index_id, document, embedding))

@router.get("/indices/{index_id}/documents", response_model=ApiResponse[List[Document]])
async def list_documents(index_id: int):
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    return success(data=DocumentRepository.list(index_id))

@router.delete("/indices/{index_id}/documents/{document_id}")
async def delete_document(index_id: int, document_id: int):
    if not DocumentRepository.delete(index_id, document_id):
        raise NotFoundException(message="文档不存在")
    return success(message="文档删除成功")

@router.post("/indices/{index_id}/rebuild", response_model=ApiResponse)
async def rebuild_index(index_id: int):
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    # 重建索引
    IndexRepository.rebuild_faiss_index(index_id)
    return success(message="索引重建成功")

@router.post("/indices/{index_id}/recall-test", response_model=ApiResponse[List[Document]])
async def recall_test(request: DocumentRecallRequest):
    # 检查索引是否存在
    index = IndexRepository.get(request.index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    # 获取查询向量
    query_embedding = embedding_service.get_embedding(request.query)
    
    # 搜索相似文档
    return success(data=DocumentRepository.search_similar(request.index_id, query_embedding, request.top_k))

@router.post("/indices/{index_id}/upload-file", response_model=ApiResponse[ProcessedFileInfo])
async def upload_file(
    index_id: int, 
    file: UploadFile = File(...),
    config_json: str = Form(...),
    metadata_json: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """
    上传文件并将其添加到索引中
    
    文件将被处理并根据指定的切片配置切分为多个文档
    
    Args:
        index_id: 索引ID
        file: 要上传的文件
        config_json: 切片配置的JSON字符串
        metadata_json: 要添加到所有文档的元数据的JSON字符串
        background_tasks: 后台任务
    """
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    # 解析切片配置
    chunking_config = parse_obj_as(ChunkingConfig, json.loads(config_json))
    
    # 解析元数据
    metadata = json.loads(metadata_json) if metadata_json else {}
    
    # 保存上传的文件
    file_path = os.path.join(TEMP_UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 处理文件
        chunks = await DocumentProcessor.process_file(file_path, chunking_config)
        
        # 将文本块转换为文档
        documents = DocumentProcessor.chunks_to_documents(chunks, metadata, file_path)
        
        # 添加文档到索引
        for doc in documents:
            # 获取文档向量
            embedding = embedding_service.get_embedding(doc.content)
            # 创建文档
            DocumentRepository.create(index_id, doc, embedding)
        
        # 创建处理结果
        result = ProcessedFileInfo(
            filename=file.filename,
            chunk_count=len(chunks),
            total_characters=sum(len(chunk) for chunk in chunks)
        )
        
        return success(data=result)
    finally:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

@router.post("/indices/{index_id}/batch-upload", response_model=ApiResponse[List[ProcessedFileInfo]])
async def batch_upload(
    index_id: int, 
    files: List[UploadFile] = File(...),
    config_json: str = Form(...),
    metadata_json: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None
):
    """
    批量上传文件并将其添加到索引中
    
    文件将被处理并根据指定的切片配置切分为多个文档
    
    Args:
        index_id: 索引ID
        files: 要上传的文件列表
        config_json: 切片配置的JSON字符串
        metadata_json: 要添加到所有文档的元数据的JSON字符串
        background_tasks: 后台任务
    """
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    # 解析切片配置
    chunking_config = parse_obj_as(ChunkingConfig, json.loads(config_json))
    
    # 解析元数据
    metadata = json.loads(metadata_json) if metadata_json else {}
    
    results = []
    
    for file in files:
        # 保存上传的文件
        file_path = os.path.join(TEMP_UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            # 处理文件
            chunks = await DocumentProcessor.process_file(file_path, chunking_config)
            
            # 将文本块转换为文档
            documents = DocumentProcessor.chunks_to_documents(chunks, metadata, file_path)
            
            # 添加文档到索引
            for doc in documents:
                # 获取文档向量
                embedding = embedding_service.get_embedding(doc.content)
                # 创建文档
                DocumentRepository.create(index_id, doc, embedding)
            
            # 创建处理结果
            result = ProcessedFileInfo(
                filename=file.filename,
                chunk_count=len(chunks),
                total_characters=sum(len(chunk) for chunk in chunks)
            )
            
            results.append(result)
        finally:
            # 删除临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
    
    return success(data=results)

@router.post("/indices/{index_id}/index-repository", response_model=ApiResponse[RepoIndexResult])
async def index_repository(index_id: int, request: RepoIndexRequest):
    """
    索引本地代码仓库
    
    处理指定目录下的所有代码文件并添加到索引中
    
    Args:
        index_id: 索引ID
        request: 请求参数，包含仓库路径、切片配置等
    """
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    # 检查仓库路径是否存在
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=400, detail=f"路径不存在: {request.repo_path}")
    
    # 处理代码仓库
    repo_results = await DocumentProcessor.process_directory(
        request.repo_path, 
        request.chunking_config, 
        request.recursive
    )
    
    # 添加文档到索引
    total_chunks = 0
    total_characters = 0
    processed_files = []
    
    for result in repo_results:
        # 添加元数据
        file_metadata = request.metadata or {}
        file_metadata.update({
            "repo_path": request.repo_path,
            "file_path": result["path"],
            "file_name": result["filename"]
        })
        
        # 将文本块转换为文档
        documents = DocumentProcessor.chunks_to_documents(
            result["chunks"], 
            file_metadata, 
            os.path.join(request.repo_path, result["path"])
        )
        
        # 添加文档到索引
        for doc in documents:
            # 获取文档向量
            embedding = embedding_service.get_embedding(doc.content)
            # 创建文档
            DocumentRepository.create(index_id, doc, embedding)
        
        # 更新统计信息
        total_chunks += result["chunk_count"]
        total_characters += result["total_characters"]
        
        # 添加到处理结果
        processed_files.append(ProcessedFileInfo(
            filename=result["path"],
            chunk_count=result["chunk_count"],
            total_characters=result["total_characters"]
        ))
    
    # 创建结果
    result = RepoIndexResult(
        total_files=len(repo_results),
        total_chunks=total_chunks,
        total_characters=total_characters,
        processed_files=processed_files
    )
    
    return success(data=result)
