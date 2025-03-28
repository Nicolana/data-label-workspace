import json
import numpy as np
import faiss
import pickle
from datetime import datetime
from typing import List, Optional
from app.db.session import get_db_cursor
from app.models.index import Index, IndexCreate, Document, DocumentCreate

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
            index_bytes = pickle.dumps(faiss_index)
            
            cursor.execute(
                "INSERT INTO vector_indices (index_id, faiss_index) VALUES (?, ?)",
                (index_id, index_bytes)
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
            return cursor.rowcount > 0

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
            cursor.execute("SELECT faiss_index FROM vector_indices WHERE index_id = ?", (index_id,))
            faiss_index = pickle.loads(cursor.fetchone()[0])
            faiss_index.add(embedding.reshape(1, -1))
            index_bytes = pickle.dumps(faiss_index)
            
            cursor.execute(
                "UPDATE vector_indices SET faiss_index = ? WHERE index_id = ?",
                (index_bytes, index_id)
            )
            
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
                    metadata=json.loads(row[2]) if row[2] else None,
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
            
            embedding = np.frombuffer(result[0], dtype=np.float32)
            
            # 删除文档
            cursor.execute(
                "DELETE FROM documents WHERE id = ? AND index_id = ?",
                (document_id, index_id)
            )
            
            if cursor.rowcount == 0:
                return False
            
            # 更新 FAISS 索引
            cursor.execute("SELECT faiss_index FROM vector_indices WHERE index_id = ?", (index_id,))
            faiss_index = pickle.loads(cursor.fetchone()[0])
            faiss_index.remove_ids(np.array([document_id]))
            index_bytes = pickle.dumps(faiss_index)
            
            cursor.execute(
                "UPDATE vector_indices SET faiss_index = ? WHERE index_id = ?",
                (index_bytes, index_id)
            )
            
            return True
    
    @staticmethod
    def search_similar(index_id: int, query_embedding: np.ndarray, k: int = 5) -> List[Document]:
        with get_db_cursor() as cursor:
            # 加载 FAISS 索引
            cursor.execute("SELECT faiss_index FROM vector_indices WHERE index_id = ?", (index_id,))
            faiss_index = pickle.loads(cursor.fetchone()[0])
            
            # 搜索相似向量
            distances, indices = faiss_index.search(query_embedding.reshape(1, -1), k)
            
            # 获取文档内容
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0:  # FAISS 返回 -1 表示没有足够的结果
                    continue
                
                cursor.execute(
                    "SELECT id, content, metadata, created_at FROM documents WHERE index_id = ? AND id = ?",
                    (index_id, idx)
                )
                row = cursor.fetchone()
                if row:
                    results.append(
                        Document(
                            id=row[0],
                            index_id=index_id,
                            content=row[1],
                            metadata=json.loads(row[2]) if row[2] else None,
                            created_at=row[3],
                            similarity=float(1 / (1 + distances[0][i]))  # 转换距离为相似度
                        )
                    )
            
            return results 