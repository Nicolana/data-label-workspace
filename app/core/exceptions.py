from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.response import ResponseStatus, error, param_error


class APIException(Exception):
    """
    API异常基类
    自定义API异常应该继承此类
    """
    def __init__(
        self,
        message: str = "操作失败",
        code: int = ResponseStatus.ERROR,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: dict = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.headers = headers
        super().__init__(self.message)


class NotFoundException(APIException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(
            message=message,
            code=ResponseStatus.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ForbiddenException(APIException):
    """禁止访问异常"""
    def __init__(self, message: str = "禁止访问"):
        super().__init__(
            message=message,
            code=ResponseStatus.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN
        )


class UnauthorizedException(APIException):
    """未授权异常"""
    def __init__(self, message: str = "未授权"):
        super().__init__(
            message=message,
            code=ResponseStatus.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


async def api_exception_handler(request: Request, exc: APIException):
    """自定义API异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None
        },
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error(
            message=exc.detail,
            code=exc.status_code
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求参数验证异常处理器"""
    errors = exc.errors()
    error_msg = "参数错误"
    
    if errors and len(errors) > 0:
        error_detail = errors[0]
        loc = error_detail.get("loc", [])
        if len(loc) > 1:
            field = loc[1]
            error_msg = f"参数 '{field}' {error_detail.get('msg', '错误')}"
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=param_error(message=error_msg)
    ) 