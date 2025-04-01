from fastapi import APIRouter, Depends, Path, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.models.response import ApiResponse, success, error, not_found
from app.core.exceptions import NotFoundException, ForbiddenException, UnauthorizedException

router = APIRouter(tags=["示例"])


class ExampleItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


# 示例数据
example_items = [
    ExampleItem(id=1, name="示例1", description="这是示例1的描述"),
    ExampleItem(id=2, name="示例2", description="这是示例2的描述"),
    ExampleItem(id=3, name="示例3", description="这是示例3的描述"),
]


@router.get("/examples", response_model=ApiResponse[List[ExampleItem]])
async def list_examples():
    """
    获取示例列表
    中间件会自动将返回结果格式化为统一响应格式
    """
    return example_items


@router.get("/examples/{example_id}", response_model=ApiResponse[ExampleItem])
async def get_example(example_id: int = Path(..., gt=0)):
    """
    获取单个示例
    演示如何手动返回统一格式响应
    """
    for item in example_items:
        if item.id == example_id:
            # 手动返回统一格式响应
            return success(data=item)
    
    # 手动返回错误响应
    return not_found(message=f"示例 {example_id} 不存在")


@router.post("/examples", response_model=ApiResponse[ExampleItem])
async def create_example(item: ExampleItem):
    """
    创建示例
    演示中间件如何自动将普通返回值转换为统一格式
    """
    # 检查ID是否已存在
    for existing_item in example_items:
        if existing_item.id == item.id:
            # 这里使用HTTPException，会被异常处理器转换为统一格式
            raise HTTPException(status_code=400, detail=f"ID {item.id} 已存在")
    
    # 模拟添加到数据库
    example_items.append(item)
    return item  # 中间件会自动将结果转换为统一格式


@router.get("/examples/error/not-found")
async def example_not_found():
    """
    演示自定义异常的使用
    """
    raise NotFoundException(message="演示资源不存在异常")


@router.get("/examples/error/forbidden")
async def example_forbidden():
    """
    演示自定义异常的使用
    """
    raise ForbiddenException(message="演示禁止访问异常")


@router.get("/examples/error/unauthorized")
async def example_unauthorized():
    """
    演示自定义异常的使用
    """
    raise UnauthorizedException(message="演示未授权异常") 