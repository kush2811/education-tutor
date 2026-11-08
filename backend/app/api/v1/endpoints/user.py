"""Endpoints for student profile management."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get user profile"
)
def get_profile(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile information for the authenticated user."""
    return current_user


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile"
)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Update student profile details such as name and grade level."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.grade_level is not None:
        current_user.grade_level = payload.grade_level
    db.commit()
    db.refresh(current_user)
    return current_user
