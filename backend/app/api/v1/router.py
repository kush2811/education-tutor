"""API v1 router aggregating all endpoints."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, session, auth, user, ingest, knowledge, rag, tutor, validation

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(session.router, tags=["Sessions & Chat"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["File Ingestion"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["Educational Knowledge Base"])
api_router.include_router(rag.router, prefix="/rag", tags=["Retrieval-Augmented Generation (RAG)"])
api_router.include_router(tutor.router, prefix="/tutor", tags=["AI Tutor & Educational Problem Solver"])
api_router.include_router(validation.router, prefix="/validation", tags=["Answer Validation & Hallucination Control"])
