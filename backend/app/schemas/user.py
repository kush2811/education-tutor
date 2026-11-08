"""Pydantic schemas for user profiles and account management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="Student email address")
    full_name: Optional[str] = Field("Student Learner", description="Student's name")
    grade_level: Optional[str] = Field("Grade 10", description="Academic level")


class UserCreate(UserBase):
    """Schema for registering a new student."""
    password: str = Field(..., min_length=6, description="Plaintext password")


class UserUpdate(BaseModel):
    """Schema for updating student profile."""
    full_name: Optional[str] = None
    grade_level: Optional[str] = None


class UserResponse(UserBase):
    """Schema for returning user data."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
