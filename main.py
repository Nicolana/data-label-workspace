from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import sqlite3
from pathlib import Path
import tiktoken
import os
from dotenv import load_dotenv
from openai import OpenAI
from fastapi.responses import StreamingResponse

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

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 创建对话表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            messages TEXT NOT NULL,
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
            FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
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

@app.post("/complete")
async def complete(request: Request):
    try:
        data = await request.json()
        messages = data.get("messages", [])
        
        if not messages:
            raise HTTPException(status_code=400, detail="消息不能为空")
            
        # 调用 OpenAI API
        async def event_generator():
            async for chunk in call_openai(messages, stream=True):
                yield chunk
        
        # 返回流式响应
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

# 添加聊天消息相关的数据模型
class ChatMessage(BaseModel):
    id: Optional[int] = None
    conversation_id: int
    role: str
    content: str
    created_at: Optional[str] = None

# 添加聊天消息相关的 API 端点
@app.post("/chat-messages")
async def create_chat_message(message: ChatMessage):
    now = datetime.now().isoformat()
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (message.conversation_id, message.role, message.content, now)
        )
        message_id = cursor.lastrowid
        
        # 更新对话的更新时间
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, message.conversation_id)
        )
        
        conn.commit()
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)