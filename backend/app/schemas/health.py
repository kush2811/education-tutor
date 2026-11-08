"""Pydantic schemas for health checks and system status."""

from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for service health status."""
    status: str = Field(..., description="Overall system health status ('healthy' or 'degraded')")
    service: str = Field(..., description="Name of the service")
    version: str = Field(..., description="API Version")
    environment: str = Field(..., description="Execution environment")
    database_status: str = Field(..., description="Status of database connectivity")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the health check")

