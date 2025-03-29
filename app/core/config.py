from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Data Label API"
    
    # 数据库配置
    DB_FILE: str = "conversations.db"
    MAX_CONNECTIONS: int = 5
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_API_HOST: Optional[str] = os.getenv("OPENAI_API_HOST")
    
    # 向量模型配置
    VECTOR_DIM: int = 384
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        case_sensitive = True

settings = Settings() 