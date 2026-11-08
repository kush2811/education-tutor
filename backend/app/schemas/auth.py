"""Pydantic schemas for authentication and tokens."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """Schema for student login."""
    email: EmailStr = Field(..., description="Student email")
    password: str = Field(..., description="Student password")


class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for decoded JWT token payload."""
    sub: str
    email: Optional[str] = None
    exp: Optional[int] = None
