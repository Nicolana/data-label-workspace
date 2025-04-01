from typing import Generic, TypeVar, Optional, Any, List, Dict, Union
from pydantic import BaseModel, Field

T = TypeVar('T')

class ResponseStatus:
    """API响应状态码定义"""
    # 成功
    SUCCESS = 0
    # 一般错误
    ERROR = 1
    # 参数错误
    PARAM_ERROR = 400
    # 未授权
    UNAUTHORIZED = 401
    # 禁止访问
    FORBIDDEN = 403
    # 资源不存在
    NOT_FOUND = 404
    # 服务器内部错误
    SERVER_ERROR = 500

class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = Field(default=ResponseStatus.SUCCESS, description="状态码")
    message: str = Field(default="操作成功", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    
    class Config:
        schema_extra = {
            "example": {
                "code": 0,
                "message": "操作成功",
                "data": None
            }
        }

class PageInfo(BaseModel):
    """分页信息"""
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")

class PageResponse(ApiResponse, Generic[T]):
    """分页响应格式"""
    data: Optional[List[T]] = Field(default=None, description="分页数据列表")
    page_info: Optional[PageInfo] = Field(default=None, description="分页信息")
    
    class Config:
        schema_extra = {
            "example": {
                "code": 0,
                "message": "操作成功",
                "data": [],
                "page_info": {
                    "total": 100,
                    "page": 1,
                    "page_size": 10,
                    "total_pages": 10
                }
            }
        }

# 一些常用响应快捷方法
def success(data: Optional[Any] = None, message: str = "操作成功") -> Dict:
    """成功响应"""
    return {
        "code": ResponseStatus.SUCCESS,
        "message": message,
        "data": data
    }

def error(message: str = "操作失败", code: int = ResponseStatus.ERROR) -> Dict:
    """错误响应"""
    return {
        "code": code,
        "message": message,
        "data": None
    }

def not_found(message: str = "资源不存在") -> Dict:
    """资源不存在响应"""
    return error(message, ResponseStatus.NOT_FOUND)

def param_error(message: str = "参数错误") -> Dict:
    """参数错误响应"""
    return error(message, ResponseStatus.PARAM_ERROR)

def server_error(message: str = "服务器内部错误") -> Dict:
    """服务器错误响应"""
    return error(message, ResponseStatus.SERVER_ERROR) 