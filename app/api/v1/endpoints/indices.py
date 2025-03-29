from fastapi import APIRouter, HTTPException
from typing import List
from app.models.index import Index, IndexCreate, Document, DocumentCreate
from app.db.repositories.index import IndexRepository, DocumentRepository
from app.services.embedding import EmbeddingService

router = APIRouter()
embedding_service = EmbeddingService()

@router.post("/indices", response_model=Index)
async def create_index(index: IndexCreate):
    return IndexRepository.create(index)

@router.get("/indices", response_model=List[Index])
async def list_indices():
    return IndexRepository.list()

@router.get("/indices/{index_id}", response_model=Index)
async def get_index(index_id: int):
    index = IndexRepository.get(index_id)
    if not index:
        raise HTTPException(status_code=404, detail="索引不存在")
    return index

@router.delete("/indices/{index_id}")
async def delete_index(index_id: int):
    if not IndexRepository.delete(index_id):
        raise HTTPException(status_code=404, detail="索引不存在")
    return {"message": "索引删除成功"}

@router.post("/indices/{index_id}/documents", response_model=Document)
async def add_document(index_id: int, document: DocumentCreate):
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise HTTPException(status_code=404, detail="索引不存在")
    
    # 获取文档向量
    embedding = embedding_service.get_embedding(document.content)
    
    # 创建文档
    return DocumentRepository.create(index_id, document, embedding)

@router.get("/indices/{index_id}/documents", response_model=List[Document])
async def list_documents(index_id: int):
    # 检查索引是否存在
    index = IndexRepository.get(index_id)
    if not index:
        raise HTTPException(status_code=404, detail="索引不存在")
    
    return DocumentRepository.list(index_id)

@router.delete("/indices/{index_id}/documents/{document_id}")
async def delete_document(index_id: int, document_id: int):
    if not DocumentRepository.delete(index_id, document_id):
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"message": "文档删除成功"} 