from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import json
from typing import Any, Dict, Union
import traceback

from app.models.response import ResponseStatus, success, error, server_error


class ResponseFormatMiddleware(BaseHTTPMiddleware):
    """
    统一响应格式中间件
    确保所有API响应都按照统一格式返回
    """
    
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # 排除不需要格式化的路径（如swagger文档相关路径）
        if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json"):
            return await call_next(request)
        
        try:
            # 调用下一个中间件或路由处理函数
            response = await call_next(request)
            
            # 如果响应已经是JSONResponse且状态码为200，并且不是健康检查接口
            if (
                isinstance(response, JSONResponse) 
                and response.status_code == 200 
                and not request.url.path.endswith("/health")
            ):
                # 获取原始响应数据
                response_body = json.loads(response.body)
                
                # 检查响应是否已经符合标准格式
                if isinstance(response_body, dict) and "code" in response_body and "message" in response_body:
                    # 已经是标准格式，直接返回
                    return response
                
                # 转换为标准格式
                formatted_response = success(data=response_body)
                return JSONResponse(content=formatted_response)
            
            return response
            
        except Exception as exc:
            # 记录异常
            error_detail = f"服务器内部错误: {str(exc)}\n{traceback.format_exc()}"
            
            # 返回统一格式的错误响应
            error_response = server_error(message="服务器内部错误，请稍后再试")
            return JSONResponse(
                status_code=500, 
                content=error_response
            ) 