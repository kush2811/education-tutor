"""Authentication endpoints for student registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.logging import logger

router = APIRouter()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to extract and validate authenticated user from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.execute(select(User).where(User.id == payload["sub"])).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists.",
        )
    return user


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency to extract authenticated user if Bearer token is provided, otherwise returns None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            return None
        return db.execute(select(User).where(User.id == payload["sub"])).scalar_one_or_none()
    except Exception:
        return None


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student account"
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """Create a new student profile with hashed password credentials."""
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    new_user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name or "Student Learner",
        grade_level=payload.grade_level or "Grade 10"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Registered new user: {new_user.email} (id={new_user.id})")
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate student and obtain access token"
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate credentials and issue an HMAC-SHA256 session token."""
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    token = create_access_token(data={"sub": user.id, "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current student profile"
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Retrieve details of the currently authenticated student."""
    return current_user

