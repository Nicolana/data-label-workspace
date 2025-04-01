from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import json
import os
import shutil
import tempfile
from datetime import datetime
import subprocess
import git
from pydantic import parse_obj_as, BaseModel, HttpUrl

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

# Git仓库临时克隆目录
GIT_CLONE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "git_repos")
os.makedirs(GIT_CLONE_DIR, exist_ok=True)

# Git仓库索引请求模型
class GitRepoIndexRequest(BaseModel):
    git_url: HttpUrl
    branch: Optional[str] = "main"
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
    
    print("开发获取查询文本向量")
    # 获取查询向量
    query_embedding = embedding_service.get_embedding(request.query)
    print("开发获取查询文本向量完成")
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

@router.post("/indices/{index_id}/index-git-repository", response_model=ApiResponse[RepoIndexResult])
async def index_git_repository(
    index_id: int,
    request: GitRepoIndexRequest
):
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise NotFoundException(message="索引不存在")
    
    # 创建唯一的临时目录
    repo_name = request.git_url.split('/')[-1].replace('.git', '')
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    clone_dir = os.path.join(GIT_CLONE_DIR, f"{repo_name}_{timestamp}")
    
    try:
        # 克隆Git仓库
        repo = git.Repo.clone_from(
            str(request.git_url),
            clone_dir,
            depth=1,
            branch=request.branch
        )
        
        # 克隆成功后处理目录
        results = await DocumentProcessor.process_directory(
            clone_dir, 
            request.chunking_config, 
            request.recursive
        )
        
        # 添加到索引
        total_chunks = 0
        processed_files = []
        
        for file_result in results:
            # 为每个文件添加元数据
            file_metadata = {
                **(request.metadata or {}),
                'git_repo': str(request.git_url),
                'git_branch': request.branch,
                'file_path': file_result['path'],
                'file_name': file_result['filename'],
                'processed_at': datetime.now().isoformat()
            }
            
            # 创建文档对象
            documents = DocumentProcessor.chunks_to_documents(
                file_result['chunks'],
                file_metadata,
                os.path.join(clone_dir, file_result['path'])
            )
            
            # 添加到数据库
            document_ids = DocumentRepository.batch_create(index_id, documents)
            
            # 记录处理信息
            total_chunks += len(documents)
            processed_files.append(
                ProcessedFileInfo(
                    filename=file_result['filename'],
                    path=file_result['path'],
                    chunks=len(documents),
                    characters=file_result['total_characters']
                )
            )
        
        # 返回结果
        return success(data=RepoIndexResult(
            total_files=len(results),
            total_chunks=total_chunks,
            total_characters=sum(f['total_characters'] for f in results),
            processed_files=processed_files
        ))
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"处理Git仓库失败: {str(e)}"
        )
    finally:
        # 清理：无论成功或失败，都尝试删除临时目录
        try:
            if os.path.exists(clone_dir):
                shutil.rmtree(clone_dir)
        except Exception as e:
            print(f"清理临时目录失败: {str(e)}")
