import json
import numpy as np
import faiss
import pickle
import os
from datetime import datetime
from typing import List, Optional
from app.db.session import get_db_cursor
from app.models.index import Index, IndexCreate, Document, DocumentCreate
from app.core.config import settings

# 创建索引文件目录
INDICES_DIR = os.path.join(os.path.dirname(settings.DB_FILE), "vector_indices")
os.makedirs(INDICES_DIR, exist_ok=True)

def get_index_file_path(index_id: int) -> str:
    """获取索引文件路径"""
    return os.path.join(INDICES_DIR, f"index_{index_id}.faiss")

class IndexRepository:
    @staticmethod
    def create(index: IndexCreate) -> Index:
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO indices (name, description) VALUES (?, ?)",
                (index.name, index.description)
            )
            index_id = cursor.lastrowid
            
            # 创建空的 FAISS 索引
            faiss_index = faiss.IndexFlatL2(384)  # 使用配置中的维度
            
            # 保存到文件系统
            faiss.write_index(faiss_index, get_index_file_path(index_id))
            
            # 记录索引元数据
            cursor.execute(
                "INSERT INTO vector_indices (index_id) VALUES (?)",
                (index_id,)
            )
            
            return Index(
                id=index_id,
                name=index.name,
                description=index.description,
                created_at=datetime.now(),
                document_count=0
            )
    
    @staticmethod
    def get(index_id: int) -> Optional[Index]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT i.id, i.name, i.description, i.created_at, COUNT(d.id) as document_count "
                "FROM indices i "
                "LEFT JOIN documents d ON i.id = d.index_id "
                "WHERE i.id = ? "
                "GROUP BY i.id",
                (index_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            return Index(
                id=row[0],
                name=row[1],
                description=row[2],
                created_at=row[3],
                document_count=row[4]
            )
    
    @staticmethod
    def list() -> List[Index]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT i.id, i.name, i.description, i.created_at, COUNT(d.id) as document_count "
                "FROM indices i "
                "LEFT JOIN documents d ON i.id = d.index_id "
                "GROUP BY i.id "
                "ORDER BY i.created_at DESC"
            )
            rows = cursor.fetchall()
            
            return [
                Index(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    created_at=row[3],
                    document_count=row[4]
                )
                for row in rows
            ]
    
    @staticmethod
    def delete(index_id: int) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM indices WHERE id = ?", (index_id,))
            if cursor.rowcount > 0:
                # 删除对应的向量索引文件
                index_file = get_index_file_path(index_id)
                if os.path.exists(index_file):
                    os.remove(index_file)
                return True
            return False
    
    @staticmethod
    def rebuild_faiss_index(index_id: int) -> bool:
        """
        重建索引的 FAISS 向量索引
        
        Args:
            index_id: 索引ID
            
        Returns:
            bool: 是否成功
        """
        with get_db_cursor() as cursor:
            # 获取所有文档
            cursor.execute(
                "SELECT id, embedding FROM documents WHERE index_id = ?",
                (index_id,)
            )
            documents = cursor.fetchall()
            
            if not documents:
                # 如果没有文档，创建空索引
                faiss_index = faiss.IndexFlatL2(384)
            else:
                # 创建新的 FAISS 索引
                faiss_index = faiss.IndexFlatL2(384)
                
                # 添加所有文档向量
                for doc_id, embedding_bytes in documents:
                    embedding = np.frombuffer(embedding_bytes, dtype=np.float32).reshape(1, -1)
                    faiss_index.add(embedding)
            
            # 保存到文件系统
            faiss.write_index(faiss_index, get_index_file_path(index_id))
            
            return True

class DocumentRepository:
    @staticmethod
    def create(index_id: int, document: DocumentCreate, embedding: np.ndarray) -> Document:
        with get_db_cursor() as cursor:
            # 插入文档
            cursor.execute(
                "INSERT INTO documents (index_id, content, metadata, embedding) VALUES (?, ?, ?, ?)",
                (index_id, document.content, json.dumps(document.metadata), embedding.tobytes())
            )
            doc_id = cursor.lastrowid
            
            # 更新 FAISS 索引
            index_file = get_index_file_path(index_id)
            if os.path.exists(index_file):
                faiss_index = faiss.read_index(index_file)
                faiss_index.add(embedding.reshape(1, -1))
                faiss.write_index(faiss_index, index_file)
            
            return Document(
                id=doc_id,
                index_id=index_id,
                content=document.content,
                metadata=document.metadata,
                created_at=datetime.now()
            )

    @staticmethod
    def list(index_id: int) -> List[Document]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, content, metadata, created_at FROM documents WHERE index_id = ? ORDER BY created_at DESC",
                (index_id,)
            )
            rows = cursor.fetchall()
            
            return [
                Document(
                    id=row[0],
                    index_id=index_id,
                    content=row[1],
                    metadata=json.loads(row[2]) if row[2] else {},
                    created_at=row[3]
                )
                for row in rows
            ]
    
    @staticmethod
    def delete(index_id: int, document_id: int) -> bool:
        with get_db_cursor() as cursor:
            # 获取文档向量
            cursor.execute(
                "SELECT embedding FROM documents WHERE id = ? AND index_id = ?",
                (document_id, index_id)
            )
            result = cursor.fetchone()
            if not result:
                return False
            
            # 删除文档
            cursor.execute(
                "DELETE FROM documents WHERE id = ? AND index_id = ?",
                (document_id, index_id)
            )
            
            if cursor.rowcount == 0:
                return False
            
            # 重建 FAISS 索引
            IndexRepository.rebuild_faiss_index(index_id)
            
            return True
    
    @staticmethod
    def search_similar(index_id: int, query_embedding: np.ndarray, k: int = 5) -> List[Document]:
        index_file = get_index_file_path(index_id)
        if not os.path.exists(index_file):
            return []
            
        # 从文件加载 FAISS 索引
        faiss_index = faiss.read_index(index_file)
        
        # 检查索引中是否有向量
        if faiss_index.ntotal == 0:
            return []
        
        # 搜索相似向量
        distances, indices = faiss_index.search(query_embedding.reshape(1, -1), min(k, faiss_index.ntotal))
        
        # 获取文档内容
        with get_db_cursor() as cursor:
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0:  # FAISS 返回 -1 表示没有足够的结果
                    continue
                
                cursor.execute(
                    "SELECT id, content, metadata, created_at FROM documents WHERE index_id = ? AND id = ?",
                    (index_id, int(idx))
                )
                row = cursor.fetchone()
                if row:
                    results.append(
                        Document(
                            id=row[0],
                            index_id=index_id,
                            content=row[1],
                            metadata=json.loads(row[2]) if row[2] else {},
                            created_at=row[3],
                            similarity=float(1 / (1 + distances[0][i]))  # 转换距离为相似度
                        )
                    )
            
            return results 