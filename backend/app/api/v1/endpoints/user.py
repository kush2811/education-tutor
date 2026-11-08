"""Endpoints for student profile and dashboard metrics."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.user import User
from app.models.session import StudySession, SessionMessage
from app.models.asset import UploadedAsset
from app.schemas.user import UserResponse, UserUpdate, DashboardStatsResponse, RecentSessionItem
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


@router.get(
    "/dashboard",
    response_model=DashboardStatsResponse,
    summary="Get student learning statistics and dashboard overview"
)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DashboardStatsResponse:
    """Aggregate student session history, uploaded assets count, and topic recommendations."""
    # Count user's sessions (or default sessions)
    sessions_query = select(StudySession).where(
        (StudySession.user_id == current_user.id) | (StudySession.student_id == current_user.id)
    ).order_by(StudySession.updated_at.desc())
    user_sessions = db.execute(sessions_query).scalars().all()
    total_sessions = len(user_sessions)

    # Count messages
    session_ids = [s.id for s in user_sessions]
    total_messages = 0
    if session_ids:
        msg_count_query = select(func.count(SessionMessage.id)).where(SessionMessage.session_id.in_(session_ids))
        total_messages = db.execute(msg_count_query).scalar_one() or 0

    # Count uploaded assets
    asset_count_query = select(func.count(UploadedAsset.id)).where(
        (UploadedAsset.user_id == current_user.id) | (UploadedAsset.session_id.in_(session_ids) if session_ids else False)
    )
    total_uploads = db.execute(asset_count_query).scalar_one() or 0

    # Recent 5 sessions
    recent_items = []
    for s in user_sessions[:5]:
        m_count = db.execute(select(func.count(SessionMessage.id)).where(SessionMessage.session_id == s.id)).scalar_one() or 0
        recent_items.append(RecentSessionItem(
            id=s.id,
            title=s.title,
            subject=s.subject,
            status=s.status,
            message_count=m_count,
            updated_at=s.updated_at
        ))

    # Grade-level tailored curriculum recommendations
    grade = current_user.grade_level.lower()
    if "11" in grade or "12" in grade:
        recs = [
            "Calculus: Chain Rule & Implicit Differentiation",
            "Physics: Conservation of Linear Momentum in 2D",
            "Chemistry: Chemical Thermodynamics & Enthalpy",
            "Mathematics: Integration by Parts & Trigonometric Substitution"
        ]
    elif "undergraduate" in grade or "college" in grade:
        recs = [
            "Linear Algebra: Eigenvalues & Diagonalization",
            "Differential Equations: Second-Order Homogeneous Equations",
            "Algorithms: Asymptotic Analysis & Master Theorem",
            "Physics: Hamiltonian Mechanics & Harmonic Oscillators"
        ]
    else:
        recs = [
            "Algebra: Solving Quadratic Equations with the Quadratic Formula",
            "Geometry: Pythagorean Theorem & Triangle Similarities",
            "Physics: Newton's Laws of Motion & Friction",
            "Coordinate Geometry: Distance and Section Formulas"
        ]

    return DashboardStatsResponse(
        user_id=current_user.id,
        full_name=current_user.full_name,
        grade_level=current_user.grade_level,
        total_sessions=total_sessions,
        total_messages=total_messages,
        total_uploads=total_uploads,
        active_streak_days=max(1, total_sessions // 2 + 1),
        recent_sessions=recent_items,
        recommended_topics=recs
    )
