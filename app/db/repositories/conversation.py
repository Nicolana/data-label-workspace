import json
from datetime import datetime
from typing import List, Optional
from app.db.session import get_db_cursor
from app.models.conversation import Conversation, Message, ChatConversation, ChatMessage
from app.utils.token import count_tokens
class ConversationRepository:
    @staticmethod
    def create(messages: List[Message]) -> Conversation:
        now = datetime.now().isoformat()
        messages_json = json.dumps([msg.dict() for msg in messages])
        
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversations (messages, created_at, updated_at) VALUES (?, ?, ?)",
                (messages_json, now, now)
            )
            conversation_id = cursor.lastrowid
            
            return Conversation(
                id=conversation_id,
                messages=messages,
                token_count=count_tokens(messages_json),
                created_at=now,
                updated_at=now
            )
    @staticmethod
    def batch_create(messages_list: List[List[Message]]) -> List[Conversation]:
        now = datetime.now().isoformat()
        conversations = []
        
        with get_db_cursor() as cursor:
            for messages in messages_list:
                messages_json = json.dumps([msg.dict() for msg in messages])
                cursor.execute(
                    "INSERT INTO conversations (messages, created_at, updated_at) VALUES (?, ?, ?)",
                    (messages_json, now, now)
                )
                conversation_id = cursor.lastrowid
                
                conversations.append(
                    Conversation(
                        id=conversation_id,
                        messages=messages,
                        created_at=now,
                        updated_at=now,
                        token_count=count_tokens(messages_json),
                        message_count=len(messages)
                    )
                )
            
            return conversations
    
    @staticmethod
    def get(conversation_id: int) -> Optional[Conversation]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, title, messages, created_at, updated_at FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            messages_data = json.loads(row[2])
            messages = [Message(**msg) for msg in messages_data]
            
            return Conversation(
                id=row[0],
                title=row[1],
                messages=messages,
                created_at=row[3],
                updated_at=row[4],
                token_count=count_tokens(messages_data),
                message_count=len(messages)
            )
    
    @staticmethod
    def list() -> List[Conversation]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT id, title, messages, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
            )
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                messages_data = json.loads(row[2])
                messages = [Message(**msg) for msg in messages_data]
                token_count = count_tokens(messages_data)
                message_count = len(messages)
                
                conversations.append(
                    Conversation(
                        id=row[0],
                        title=row[1],
                        messages=messages,
                        created_at=row[3],
                        updated_at=row[4],
                        token_count=token_count,
                        message_count=message_count
                    )
                )
            return conversations
    
    @staticmethod
    def delete(conversation_id: int) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            return cursor.rowcount > 0
        
    @staticmethod
    def copy(conversation_id: int) -> Optional[Conversation]:
        with get_db_cursor() as cursor:
            # 获取原始对话
            cursor.execute(
                "SELECT title, messages FROM conversations WHERE id = ?", 
                (conversation_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
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
            
            # 获取新对话的完整信息
            cursor.execute(
                "SELECT id, title, messages, created_at, updated_at FROM conversations WHERE id = ?", 
                (new_id,)
            )
            new_row = cursor.fetchone()
            messages = [Message(**msg) for msg in json.loads(new_row[2])]
            
            return Conversation(
                id=new_row[0],
                title=new_row[1],
                messages=messages,
                created_at=new_row[3],
                updated_at=new_row[4]
            )
    @staticmethod
    def update(conversation_id: int, conversation: Conversation) -> Optional[Conversation]:
        with get_db_cursor() as cursor:
            now = datetime.now().isoformat()
            messages_json = json.dumps([msg.dict() for msg in conversation.messages])
            
            cursor.execute(
                "UPDATE conversations SET title = ?, messages = ?, updated_at = ? WHERE id = ?",
                (conversation.title, messages_json, now, conversation_id)
            )
            
            if cursor.rowcount == 0:
                return None
                
            return Conversation(
                id=conversation_id,
                title=conversation.title,
                messages=conversation.messages,
                updated_at=now
            )

class ChatConversationRepository:
    @staticmethod
    def create(title: str) -> ChatConversation:
        now = datetime.now().isoformat()
        
        with get_db_cursor() as cursor:
            cursor.execute(
                "INSERT INTO chat_conversations (title, created_at, updated_at) VALUES (?, ?, ?)",
                (title, now, now)
            )
            conversation_id = cursor.lastrowid
            
            return ChatConversation(
                id=conversation_id,
                title=title,
                created_at=now,
                updated_at=now
            )
    
    @staticmethod
    def get(conversation_id: int) -> Optional[ChatConversation]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) as message_count "
                "FROM chat_conversations c "
                "LEFT JOIN chat_messages m ON c.id = m.conversation_id "
                "WHERE c.id = ? "
                "GROUP BY c.id",
                (conversation_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            return ChatConversation(
                id=row[0],
                title=row[1],
                created_at=row[2],
                updated_at=row[3],
                message_count=row[4]
            )
    
    @staticmethod
    def list() -> List[ChatConversation]:
        with get_db_cursor() as cursor:
            cursor.execute(
                "SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) as message_count "
                "FROM chat_conversations c "
                "LEFT JOIN chat_messages m ON c.id = m.conversation_id "
                "GROUP BY c.id "
                "ORDER BY c.updated_at DESC"
            )
            rows = cursor.fetchall()
            
            return [
                ChatConversation(
                    id=row[0],
                    title=row[1],
                    created_at=row[2],
                    updated_at=row[3],
                    message_count=row[4]
                )
                for row in rows
            ]
    
    @staticmethod
    def delete(conversation_id: int) -> bool:
        with get_db_cursor() as cursor:
            cursor.execute("DELETE FROM chat_conversations WHERE id = ?", (conversation_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def update_title(conversation_id: int, title: str) -> Optional[ChatConversation]:
        now = datetime.now().isoformat()
        
        with get_db_cursor() as cursor:
            cursor.execute(
                "UPDATE chat_conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, now, conversation_id)
            )
            if cursor.rowcount == 0:
                return None
            
            return ChatConversationRepository.get(conversation_id) 