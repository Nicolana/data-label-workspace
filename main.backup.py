from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import sqlite3
from pathlib import Path
import tiktoken
import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.responses import StreamingResponse
import numpy as np
import faiss
import openai
import io
import pickle
from sentence_transformers import SentenceTransformer
import torch
from contextlib import contextmanager
from queue import Queue
from threading import Lock

# 加载环境变量
load_dotenv()

app = FastAPI()

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_HOST = os.getenv("OPENAI_API_HOST")
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_HOST)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库初始化
DB_FILE = "conversations.db"
MAX_CONNECTIONS = 5
connection_pool = Queue(maxsize=MAX_CONNECTIONS)
init_lock = Lock()

def init_connection_pool():
    """初始化连接池"""
    with init_lock:
        if connection_pool.empty():
            for _ in range(MAX_CONNECTIONS):
                conn = sqlite3.connect(DB_FILE, check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.row_factory = sqlite3.Row
                connection_pool.put(conn)

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    init_connection_pool()
    conn = connection_pool.get()
    try:
        yield conn
    finally:
        connection_pool.put(conn)

@contextmanager
def get_db_cursor():
    """获取数据库游标的上下文管理器"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 创建训练数据对话表（保持原有表不变）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        
        # 创建聊天对话表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        
        # 创建聊天消息表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES chat_conversations (id) ON DELETE CASCADE
        )
        """)
        
        # 创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_id 
        ON chat_messages (conversation_id)
        """)
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at 
        ON chat_messages (created_at)
        """)
        
        # 创建索引表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS indices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建文档表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (index_id) REFERENCES indices (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建向量索引表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vector_indices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            index_id INTEGER NOT NULL UNIQUE,
            faiss_index BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (index_id) REFERENCES indices (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()

init_db()

# 计算 token 数量
def count_tokens(messages: List[dict]) -> int:
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    total_tokens = 0
    
    for message in messages:
        # 计算消息内容的 tokens
        total_tokens += len(enc.encode(message["content"]))
        
        # 计算角色名称的 tokens
        total_tokens += len(enc.encode(message["role"]))
        
        # 添加一些系统消息的 tokens
        if message["role"] == "system":
            total_tokens += 4
        elif message["role"] == "user":
            total_tokens += 4
        elif message["role"] == "assistant":
            total_tokens += 4
    
    return total_tokens

# 数据模型
class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    id: Optional[int] = None
    title: str
    messages: List[Message]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = 4000
    temperature: Optional[float] = 0.7

# OpenAI API 调用
async def call_openai(messages, stream=False, temperature=0.7, max_tokens=4000):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if stream:
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
        else:
            yield f"data: {json.dumps({'content': response.choices[0].message.content})}\n\n"
                
    except Exception as e:
        if stream:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        raise e

@app.post("/generate")
async def generate_conversation(request: GenerateRequest):
    try:
        # 构建消息
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        # 调用 OpenAI API
        response_content = ""
        async for chunk in call_openai(
            messages=messages,
            stream=False,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        ):
            data = json.loads(chunk.split('data: ')[1])
            if 'content' in data:
                response_content = data['content']
        
        # 创建对话
        messages.append({"role": "assistant", "content": response_content})
        
        # 生成标题
        title = f"GPT-4 对话 {datetime.now().strftime('%Y%m%d %H%M%S')}"
        
        # 保存到数据库
        now = datetime.now().isoformat()
        messages_json = json.dumps(messages)
        
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (title, messages, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title, messages_json, now, now)
            )
            conversation_id = cursor.lastrowid
            conn.commit()
        
        return {
            "id": conversation_id,
            "title": title,
            "messages": messages,
            "created_at": now,
            "updated_at": now
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API端点
@app.get("/conversations")
def list_conversations():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, messages, created_at, updated_at FROM conversations ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conversations = []
        for row in rows:
            messages = json.loads(row[2])
            token_count = count_tokens(messages)
            conversations.append({
                "id": row[0],
                "title": row[1],
                "created_at": row[3],
                "updated_at": row[4],
                "token_count": token_count,
                "message_count": len(messages)
            })
        return conversations

@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, messages, created_at, updated_at FROM conversations WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = json.loads(row[2])
        token_count = count_tokens(messages)
        return {
            "id": row[0],
            "title": row[1],
            "messages": messages,
            "created_at": row[3],
            "updated_at": row[4],
            "token_count": token_count,
            "message_count": len(messages)
        }

@app.post("/conversations")
def create_conversation(conversation: Conversation):
    now = datetime.now().isoformat()
    messages_json = json.dumps([msg.dict() for msg in conversation.messages])
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (title, messages, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conversation.title, messages_json, now, now)
        )
        conversation_id = cursor.lastrowid
        conn.commit()
    
    return {"id": conversation_id, "title": conversation.title, "created_at": now, "updated_at": now}

@app.put("/conversations/{conversation_id}")
def update_conversation(conversation_id: int, conversation: Conversation):
    now = datetime.now().isoformat()
    messages_json = json.dumps([msg.dict() for msg in conversation.messages])
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE conversations SET title = ?, messages = ?, updated_at = ? WHERE id = ?",
            (conversation.title, messages_json, now, conversation_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conn.commit()
    
    return {"id": conversation_id, "title": conversation.title, "updated_at": now}

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conn.commit()
    
    return {"message": "Conversation deleted successfully"}

@app.get("/conversations/{conversation_id}/export")
def export_conversation(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT title, messages FROM conversations WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        title = row[0]
        messages = json.loads(row[1])
        
        # 按照对话格式返回
        return {
            "title": title,
            "messages": messages
        }

@app.post("/conversations/{conversation_id}/copy")
def copy_conversation(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 获取原始对话
        cursor.execute("SELECT title, messages FROM conversations WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # 创建新标题
        original_title = row[0]
        new_title = f"{original_title} (副本)"
        
        # 插入新对话
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO conversations (title, messages, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (new_title, row[1], now, now)
        )
        new_id = cursor.lastrowid
        conn.commit()
        
        # 获取新对话的完整信息
        cursor.execute("SELECT id, title, messages, created_at, updated_at FROM conversations WHERE id = ?", (new_id,))
        row = cursor.fetchone()
        messages = json.loads(row[2])
        token_count = count_tokens(messages)
        
        return {
            "id": row[0],
            "title": row[1],
            "messages": messages,
            "created_at": row[3],
            "updated_at": row[4],
            "token_count": token_count,
            "message_count": len(messages)
        }

# @app.post("/complete")
# async def complete(request: Request):
#     try:
#         data = await request.json()
#         messages = data.get("messages", [])
        
#         if not messages:
#             raise HTTPException(status_code=400, detail="消息不能为空")
            
#         # 调用 OpenAI API
#         async def event_generator():
#             async for chunk in call_openai(messages, stream=True):
#                 yield chunk
        
#         # 返回流式响应
#         return StreamingResponse(
#             event_generator(),
#             media_type="text/event-stream",
#             headers={
#                 "Cache-Control": "no-cache",
#                 "Connection": "keep-alive",
#             }
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# 修改 complete 路由以支持 RAG
@app.post("/complete")
async def complete(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        index_id = data.get("index_id")  # 可选的索引 ID
        
        # 获取最后一条用户消息
        user_message = next((msg["content"] for msg in reversed(messages) 
                           if msg["role"] == "user"), None)
        
        if not user_message:
            raise HTTPException(status_code=400, detail="没有找到用户消息")
        
        # 如果指定了索引，进行相似文档检索
        context = ""
        if index_id:
            similar_docs = search_similar_documents(user_message, index_id)
            if similar_docs:
                context = "相关文档内容：\n" + "\n".join(
                    f"- {doc['content']} (相似度: {doc['similarity']:.2f})"
                    for doc in similar_docs
                )
        
        # 构建系统提示
        system_prompt = """你是一个有帮助的 AI 助手。请基于以下信息回答问题：
1. 如果提供了相关文档内容，请优先使用这些信息
2. 如果相关文档内容不足，可以使用你的通用知识
3. 请明确标注信息来源（是来自相关文档还是通用知识）
4. 如果信息不足，请明确说明

"""
        
        # 添加上下文到消息列表
        if context:
            messages.insert(0, {"role": "system", "content": system_prompt + context})
        
        # 调用 OpenAI API
        async def event_generator():
            async for chunk in call_openai(messages, stream=True):
                yield chunk
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 添加聊天对话相关的数据模型
class ChatConversation(BaseModel):
    id: Optional[int] = None
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# 添加聊天对话相关的 API 端点
@app.post("/chat-conversations")
def create_chat_conversation(conversation: ChatConversation):
    now = datetime.now().isoformat()
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_conversations (title, created_at, updated_at) VALUES (?, ?, ?)",
            (conversation.title, now, now)
        )
        conversation_id = cursor.lastrowid
        conn.commit()
    
    return {
        "id": conversation_id,
        "title": conversation.title,
        "created_at": now,
        "updated_at": now
    }

@app.get("/chat-conversations")
def list_chat_conversations():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at, 
                   COUNT(m.id) as message_count
            FROM chat_conversations c
            LEFT JOIN chat_messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
        """)
        rows = cursor.fetchall()
        conversations = []
        for row in rows:
            conversations.append({
                "id": row[0],
                "title": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "message_count": row[4]
            })
        return conversations

@app.get("/chat-conversations/{conversation_id}")
def get_chat_conversation(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.title, c.created_at, c.updated_at
            FROM chat_conversations c
            WHERE c.id = ?
        """, (conversation_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # 获取消息列表
        cursor.execute("""
            SELECT role, content, created_at
            FROM chat_messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conversation_id,))
        messages = []
        for msg_row in cursor.fetchall():
            messages.append({
                "role": msg_row[0],
                "content": msg_row[1],
                "created_at": msg_row[2]
            })
        
        return {
            "id": row[0],
            "title": row[1],
            "messages": messages,
            "created_at": row[2],
            "updated_at": row[3],
            "message_count": len(messages)
        }

@app.delete("/chat-conversations/{conversation_id}")
def delete_chat_conversation(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_conversations WHERE id = ?", (conversation_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conn.commit()
    
    return {"message": "Conversation deleted successfully"}

@app.put("/chat-conversations/{conversation_id}/title")
def update_chat_conversation_title(conversation_id: int, title: str):
    now = datetime.now().isoformat()
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE chat_conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, conversation_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conn.commit()
    
    return {"id": conversation_id, "title": title, "updated_at": now}

# 添加聊天消息相关的数据模型
class ChatMessage(BaseModel):
    id: Optional[int] = None
    conversation_id: int
    role: str
    content: str
    created_at: Optional[str] = None

# 修改聊天消息相关的 API 端点
@app.post("/chat-messages")
async def create_chat_message(message: ChatMessage):
    now = datetime.now().isoformat()
    
    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO chat_messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (message.conversation_id, message.role, message.content, now)
        )
        message_id = cursor.lastrowid
        
        # 更新对话的更新时间
        cursor.execute(
            "UPDATE chat_conversations SET updated_at = ? WHERE id = ?",
            (now, message.conversation_id)
        )
        
    
    return {
        "id": message_id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "created_at": now
    }

@app.get("/chat-messages/{conversation_id}")
def get_chat_messages(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role, content, created_at FROM chat_messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,)
        )
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "role": row[1],
                "content": row[2],
                "created_at": row[3]
            })
        
        return messages

@app.delete("/chat-messages/{conversation_id}")
def delete_chat_messages(conversation_id: int):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conversation_id,))
        conn.commit()
    
    return {"message": "Chat messages deleted successfully"}

# 初始化 sentence transformer 模型
model = SentenceTransformer('all-MiniLM-L6-v2')
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)

# 向量维度
VECTOR_DIM = 384

def get_embedding(text: str) -> np.ndarray:
    """获取文本的向量表示"""
    with torch.no_grad():
        embedding = model.encode(text, convert_to_numpy=True)
    return embedding.astype(np.float32)

def create_faiss_index(embeddings: List[np.ndarray]) -> faiss.IndexFlatL2:
    """创建 FAISS 索引"""
    index = faiss.IndexFlatL2(VECTOR_DIM)
    if embeddings:
        index.add(np.vstack(embeddings))
    return index

def save_faiss_index(index: faiss.Index, cursor: sqlite3.Cursor, index_id: int):
    """保存 FAISS 索引到数据库"""
    # 序列化索引
    index_bytes = pickle.dumps(index)
    
    # 更新或插入向量索引
    cursor.execute('''
    INSERT OR REPLACE INTO vector_indices (index_id, faiss_index, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    ''', (index_id, index_bytes))
    

def load_faiss_index(db_path: str, index_id: int) -> Optional[faiss.IndexFlatL2]:
    """从数据库加载 FAISS 索引"""
    with get_db_cursor() as cursor:
        
        cursor.execute('SELECT faiss_index FROM vector_indices WHERE index_id = ?', (index_id,))
        result = cursor.fetchone()
    
        if result:
            return pickle.loads(result[0])
        return None

def search_similar_documents(query: str, index_id: int, k: int = 5) -> List[Dict[str, Any]]:
    """搜索相似文档"""
    with get_db_cursor() as cursor:
        # 加载 FAISS 索引
        faiss_index = load_faiss_index(DB_FILE, index_id)
        if not faiss_index:
            return []
        
        # 获取查询向量
        query_vector = get_embedding(query)
        
        # 搜索相似向量
        distances, indices = faiss_index.search(query_vector.reshape(1, -1), k)
        
        # 获取文档内容
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:  # FAISS 返回 -1 表示没有足够的结果
                continue
                
            cursor.execute('''
            SELECT id, content, metadata, created_at
            FROM documents
            WHERE index_id = ? AND id = ?
            ''', (index_id, idx))
            
            doc = cursor.fetchone()
            if doc:
                results.append({
                    'id': doc[0],
                    'content': doc[1],
                    'metadata': json.loads(doc[2]) if doc[2] else {},
                    'created_at': doc[3],
                    'similarity': float(1 / (1 + distances[0][i]))  # 转换距离为相似度
                })
        
        return results

# 索引管理相关的 Pydantic 模型
class IndexCreate(BaseModel):
    name: str
    description: Optional[str] = None

class DocumentCreate(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class Document(BaseModel):
    id: int
    content: str
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class Index(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    document_count: int

    class Config:
        from_attributes = True

# 索引管理 API 端点
@app.post("/indices", response_model=Index)
async def create_index(index: IndexCreate):
    with get_db_cursor() as cursor:
        cursor.execute('''
        INSERT INTO indices (name, description)
        VALUES (?, ?)
        ''', (index.name, index.description))
        
        index_id = cursor.lastrowid
        
        # 创建空的 FAISS 索引
        faiss_index = create_faiss_index([])
        save_faiss_index(faiss_index, cursor, index_id)
        
        # conn.commit()

        return {
            "id": index_id,
            "name": index.name,
            "description": index.description,
            "created_at": datetime.now(),
            "document_count": 0
        }
 

@app.get("/indices", response_model=List[Index])
async def list_indices():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT i.id, i.name, i.description, i.created_at, COUNT(d.id) as document_count
    FROM indices i
    LEFT JOIN documents d ON i.id = d.index_id
    GROUP BY i.id
    ORDER BY i.created_at DESC
    ''')
    
    indices = []
    for row in cursor.fetchall():
        indices.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
            "document_count": row[4]
        })
    
    conn.close()
    return indices

@app.delete("/indices/{index_id}")
async def delete_index(index_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM indices WHERE id = ?', (index_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="索引不存在")
    
    conn.commit()
    conn.close()
    return {"message": "索引删除成功"}

@app.post("/indices/{index_id}/documents", response_model=Document)
async def add_document(index_id: int, document: DocumentCreate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 检查索引是否存在
        cursor.execute('SELECT id FROM indices WHERE id = ?', (index_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="索引不存在")
        
        # 获取文档向量
        embedding = get_embedding(document.content)
        
        # 插入文档
        cursor.execute('''
        INSERT INTO documents (index_id, content, metadata, embedding)
        VALUES (?, ?, ?, ?)
        ''', (index_id, document.content, json.dumps(document.metadata), embedding.tobytes()))
        
        doc_id = cursor.lastrowid
        
        # 更新 FAISS 索引
        faiss_index = load_faiss_index(DB_FILE, index_id)
        faiss_index.add(embedding.reshape(1, -1))
        save_faiss_index(faiss_index, DB_FILE, index_id)
        
        conn.commit()
        
        return {
            "id": doc_id,
            "content": document.content,
            "metadata": document.metadata,
            "created_at": datetime.now()
        }
    finally:
        conn.close()

@app.get("/indices/{index_id}/documents", response_model=List[Document])
async def list_documents(index_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, content, metadata, created_at
    FROM documents
    WHERE index_id = ?
    ORDER BY created_at DESC
    ''', (index_id,))
    
    documents = []
    for row in cursor.fetchall():
        documents.append({
            "id": row[0],
            "content": row[1],
            "metadata": json.loads(row[2]) if row[2] else None,
            "created_at": row[3]
        })
    
    conn.close()
    return documents

@app.delete("/indices/{index_id}/documents/{document_id}")
async def delete_document(index_id: int, document_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 获取文档向量
        cursor.execute('SELECT embedding FROM documents WHERE id = ? AND index_id = ?', 
                      (document_id, index_id))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        embedding = np.frombuffer(result[0], dtype=np.float32)
        
        # 删除文档
        cursor.execute('DELETE FROM documents WHERE id = ? AND index_id = ?', 
                      (document_id, index_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 更新 FAISS 索引
        faiss_index = load_faiss_index(DB_FILE, index_id)
        faiss_index.remove_ids(np.array([document_id]))
        save_faiss_index(faiss_index, DB_FILE, index_id)
        
        conn.commit()
        return {"message": "文档删除成功"}
    finally:
        conn.close()

@app.post("/indices/{index_id}/rebuild")
async def rebuild_index(index_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # 获取所有文档向量
        cursor.execute('SELECT embedding FROM documents WHERE index_id = ?', (index_id,))
        embeddings = []
        for row in cursor.fetchall():
            embedding = np.frombuffer(row[0], dtype=np.float32)
            embeddings.append(embedding)
        
        # 创建新的 FAISS 索引
        if embeddings:
            faiss_index = create_faiss_index(embeddings)
            save_faiss_index(faiss_index, DB_FILE, index_id)
        
        return {"message": "索引重建成功"}
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)