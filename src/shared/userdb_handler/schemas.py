from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for creating a new user with validation."""
    email: EmailStr
    hashed_password: str = Field(min_length=1)
    tenant_id: str = Field(min_length=1)
    dept: str = Field(min_length=1)
    project: str = Field(min_length=1)
    clearance: int = Field(ge=0)


class UserUpdate(BaseModel):
    """Schema for updating user fields with validation."""
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = Field(None, min_length=1)
    tenant_id: Optional[str] = Field(None, min_length=1)
    dept: Optional[str] = Field(None, min_length=1)
    project: Optional[str] = Field(None, min_length=1)
    clearance: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class RefreshTokenCreate(BaseModel):
    user_id: str
    token: str
    expires_at: datetime


