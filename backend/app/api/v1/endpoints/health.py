"""Health check and readiness verification endpoint."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System and Database Health Check",
    description="Validates API responsiveness and database connectivity."
)
def check_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Verifies that the API service and its underlying database are running properly."""
    db_status = "connected"
    system_status = "healthy"

    try:
        # Simple test query to ensure database connection is responsive
        db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(f"Database health check failed: {str(exc)}")
        db_status = f"unhealthy: {str(exc)}"
        system_status = "degraded"

    return HealthResponse(
        status=system_status,
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database_status=db_status,
    )
