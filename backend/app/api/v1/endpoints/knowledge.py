"""API endpoints for educational knowledge base, sources, documents, chunk indexing, and curriculum search."""

import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.knowledge import EducationalSource, KnowledgeDocument, QualityReport
from app.schemas.knowledge import (
    EducationalSourceCreate,
    EducationalSourceResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentDetailResponse,
    DocumentIngestResponse,
    QualityReportResponse,
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
)
from app.services.knowledge_sources import (
    seed_default_sources,
    validate_source_license_compliance,
)
from app.services.knowledge_manager import knowledge_manager
from app.core.file_security import get_safe_storage_path, validate_file_security
from app.core.logging import logger

router = APIRouter()


@router.get(
    "/sources",
    response_model=List[EducationalSourceResponse],
    summary="List all registered educational sources"
)
def list_educational_sources(
    subject: Optional[str] = Query(None, description="Filter by subject domain"),
    academic_level: Optional[str] = Query(None, description="Filter by academic level"),
    authority_category: Optional[str] = Query(None, description="Filter by category (ncert, university, etc.)"),
    db: Session = Depends(get_db)
) -> List[EducationalSource]:
    """Retrieve registered authoritative educational sources. Auto-seeds defaults on initial access."""
    # Ensure default verified sources are seeded
    seed_default_sources(db)

    query = db.query(EducationalSource)
    if subject:
        query = query.filter(EducationalSource.subject.ilike(f"%{subject}%"))
    if academic_level:
        query = query.filter(EducationalSource.academic_level.ilike(f"%{academic_level}%"))
    if authority_category:
        query = query.filter(EducationalSource.authority_category == authority_category)

    return query.order_by(EducationalSource.source_name).all()


@router.post(
    "/sources",
    response_model=EducationalSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new authoritative educational source"
)
def register_educational_source(
    payload: EducationalSourceCreate,
    db: Session = Depends(get_db)
) -> EducationalSource:
    """Register an educational repository after verifying legal license compliance."""
    source_id = payload.id or payload.source_name.lower().replace(" ", "-").replace("(", "").replace(")", "")

    # Check duplicate
    existing = db.query(EducationalSource).filter(EducationalSource.id == source_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Educational source with ID '{source_id}' is already registered."
        )

    # License validation
    compliance = validate_source_license_compliance(
        license_type=payload.license_type,
        authority_category=payload.authority_category,
        source_url=payload.source_url
    )
    if not compliance["is_compliant"]:
        reasons_str = "; ".join(compliance["reasons"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source failed legal compliance verification: {reasons_str}"
        )

    new_source = EducationalSource(
        id=source_id,
        source_name=payload.source_name,
        source_url=payload.source_url,
        subject=payload.subject,
        academic_level=payload.academic_level,
        license_type=payload.license_type,
        source_authority=payload.source_authority,
        authority_category=payload.authority_category,
        description=payload.description,
        is_active=True,
        document_count=0
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    logger.info(f"Registered new authoritative educational source: '{new_source.source_name}' ({new_source.id})")
    return new_source


@router.get(
    "/sources/{source_id}",
    response_model=EducationalSourceResponse,
    summary="Get details of a specific educational source"
)
def get_educational_source(source_id: str, db: Session = Depends(get_db)) -> EducationalSource:
    """Retrieve details for a registered educational source by its unique ID."""
    source = db.query(EducationalSource).filter(EducationalSource.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Educational source '{source_id}' not found."
        )
    return source


@router.post(
    "/documents/ingest",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest and index an educational document (PDF, DOCX, HTML, TXT)"
)
async def ingest_educational_document(
    source_id: str = Form(..., description="ID of the registered educational source"),
    title: Optional[str] = Form(None, description="Document title or chapter heading"),
    file: UploadFile = File(..., description="Educational document file"),
    db: Session = Depends(get_db)
) -> DocumentIngestResponse:
    """Upload an academic document, extract text/math/tables, generate semantic chunks,
    create vector embeddings, and index into ChromaDB."""
    # Validate source exists
    source = db.query(EducationalSource).filter(EducationalSource.id == source_id).first()
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registered source '{source_id}' not found."
        )

    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "curriculum_doc.pdf",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes
    )

    dest_path = get_safe_storage_path("documents", safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    try:
        response = knowledge_manager.add_document(
            source_id=source_id,
            file_path=dest_path,
            title=title or file.filename,
            db=db
        )
        return response
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}")
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get(
    "/documents",
    response_model=List[KnowledgeDocumentResponse],
    summary="List all ingested curriculum documents"
)
def list_documents(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    db: Session = Depends(get_db)
) -> List[KnowledgeDocument]:
    """List indexed educational documents and chapter modules."""
    query = db.query(KnowledgeDocument)
    if source_id:
        query = query.filter(KnowledgeDocument.source_id == source_id)
    return query.order_by(KnowledgeDocument.created_at.desc()).all()


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentDetailResponse,
    summary="Get detailed metadata and chunks of an ingested document"
)
def get_document_detail(document_id: str, db: Session = Depends(get_db)) -> KnowledgeDocument:
    """Retrieve full details of an indexed educational document including all concept chunks."""
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document '{document_id}' not found."
        )
    return doc


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Purge an educational document and remove from vector store"
)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete an educational document and purge its vector embeddings from ChromaDB."""
    success = knowledge_manager.remove_document(document_id, db=db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document '{document_id}' not found."
        )
    return {"status": "success", "message": f"Document '{document_id}' successfully removed."}


@router.post(
    "/documents/{document_id}/reindex",
    response_model=DocumentIngestResponse,
    summary="Re-index an updated document and increment version"
)
def reindex_document(document_id: str, db: Session = Depends(get_db)) -> DocumentIngestResponse:
    """Re-extract and re-index an existing document, updating its version."""
    try:
        return knowledge_manager.reindex_document(document_id, db=db)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/query",
    response_model=KnowledgeQueryResponse,
    summary="Search curriculum knowledge base with verifiable citations"
)
def query_curriculum(
    payload: KnowledgeQueryRequest,
    db: Session = Depends(get_db)
) -> KnowledgeQueryResponse:
    """Execute semantic search against the curriculum vector database and return grounded excerpts with citations."""
    return knowledge_manager.search_curriculum(
        query=payload.query,
        db=db,
        subject=payload.subject,
        academic_level=payload.academic_level,
        source_id=payload.source_id,
        top_k=payload.top_k
    )


@router.get(
    "/quality/reports",
    response_model=List[QualityReportResponse],
    summary="List data quality validation reports"
)
def list_quality_reports(
    status_filter: Optional[str] = Query(None, description="Filter by status (passed, flagged_warnings, failed)"),
    db: Session = Depends(get_db)
) -> List[QualityReport]:
    """Audit reports recording missing text, duplicate chunks, and metadata errors."""
    query = db.query(QualityReport)
    if status_filter:
        query = query.filter(QualityReport.status == status_filter)
    return query.order_by(QualityReport.created_at.desc()).limit(100).all()
