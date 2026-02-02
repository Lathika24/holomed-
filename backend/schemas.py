"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    subscription_tier: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ModelCreate(BaseModel):
    name: Optional[str] = None

class ModelResponse(BaseModel):
    id: int
    name: str
    file_path: str
    file_format: str
    file_size: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    model_id: int

class SessionResponse(BaseModel):
    id: int
    user_id: int
    model_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    
    class Config:
        from_attributes = True
