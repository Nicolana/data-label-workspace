from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import sqlite3
from pathlib import Path
import tiktoken

app = FastAPI()

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

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)