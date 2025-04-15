from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.api.v1.endpoints import chat_conversations, conversations, indices, example
from app.db.migrations import init_db
from app.core.middlewares import ResponseFormatMiddleware
from app.core.exceptions import (
    APIException, 
    api_exception_handler, 
    http_exception_handler, 
    validation_exception_handler
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加统一响应格式中间件
app.add_middleware(ResponseFormatMiddleware)

# 注册异常处理器
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
# app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 注册路由
app.include_router(conversations.router, prefix=settings.API_V1_STR)
app.include_router(indices.router, prefix=settings.API_V1_STR)
app.include_router(example.router, prefix=settings.API_V1_STR)
app.include_router(chat_conversations.router, prefix=settings.API_V1_STR)

# 初始化数据库
init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 