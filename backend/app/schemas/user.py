"""Pydantic schemas for user profiles and account management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr = Field(..., description="Student email address")
    full_name: Optional[str] = Field("Student Learner", description="Student's name")
    grade_level: Optional[str] = Field("Grade 10", description="Academic level")
    preferred_explanation_level: Optional[str] = Field("intermediate", description="beginner, intermediate, advanced")
    preferred_voice: Optional[str] = Field("en-US-AriaNeural", description="Neural voice identifier")
    preferred_playback_speed: Optional[float] = Field(1.0, ge=0.5, le=3.0, description="Voice playback speed")
    preferred_language: Optional[str] = Field("en", description="Preferred language code")
    preferred_subjects: Optional[str] = Field("Mathematics,Physics,Computer Science", description="Comma-separated subjects")


class UserCreate(UserBase):
    """Schema for registering a new student."""
    password: str = Field(..., min_length=6, description="Plaintext password")


class UserUpdate(BaseModel):
    """Schema for updating student profile."""
    full_name: Optional[str] = None
    grade_level: Optional[str] = None
    preferred_explanation_level: Optional[str] = None
    preferred_voice: Optional[str] = None
    preferred_playback_speed: Optional[float] = None
    preferred_language: Optional[str] = None
    preferred_subjects: Optional[str] = None


class StudentPreferences(BaseModel):
    """Student personalization preferences."""
    preferred_explanation_level: str = "intermediate"
    preferred_voice: str = "en-US-AriaNeural"
    preferred_playback_speed: float = 1.0
    preferred_language: str = "en"
    preferred_subjects: list[str] = ["Mathematics", "Physics", "Computer Science"]


class StudentPreferencesUpdate(BaseModel):
    """Payload to update student personalization preferences."""
    preferred_explanation_level: Optional[str] = None
    preferred_voice: Optional[str] = None
    preferred_playback_speed: Optional[float] = None
    preferred_language: Optional[str] = None
    preferred_subjects: Optional[list[str]] = None


class UserResponse(UserBase):
    """Schema for returning user data."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecentSessionItem(BaseModel):
    """Brief session item for dashboard."""
    id: str
    title: str
    subject: str
    status: str
    message_count: int
    updated_at: datetime


class DashboardStatsResponse(BaseModel):
    """Aggregated learning metrics for student dashboard."""
    user_id: str
    full_name: str
    grade_level: str
    total_sessions: int
    total_messages: int
    total_uploads: int
    active_streak_days: int
    recent_sessions: list[RecentSessionItem]
    recommended_topics: list[str]

