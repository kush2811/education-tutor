"""API v1 router aggregating all endpoints."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, session

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(session.router, tags=["Sessions"])
