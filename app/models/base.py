from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaseDBModel(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 