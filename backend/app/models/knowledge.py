"""Database models for educational knowledge base, sources, documents, and chunks."""

from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class EducationalSource(Base):
    """Registry of verified, authoritative, and legally compliant educational sources."""
    
    __tablename__ = "educational_sources"

    id = Column(String(100), primary_key=True, index=True)  # e.g., 'ncert-math-class10'
    source_name = Column(String(255), nullable=False)
    source_url = Column(String(500), nullable=False)
    subject = Column(String(100), nullable=False, index=True)
    academic_level = Column(String(100), nullable=False, index=True)
    license_type = Column(String(255), nullable=False)
    collection_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    source_authority = Column(String(255), nullable=False)
    authority_category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    document_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    documents = relationship("KnowledgeDocument", back_populates="source", cascade="all, delete-orphan")


class KnowledgeDocument(Base):
    """An ingested educational document (textbook chapter, syllabus, open course module)."""

    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(100), ForeignKey("educational_sources.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, html, text
    file_size = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    total_pages = Column(Integer, default=1, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="indexed", nullable=False)  # indexed, failed, pending, archived
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    source = relationship("EducationalSource", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Concept-aware educational text chunk with exact pedagogical and citation metadata."""

    __tablename__ = "document_chunks"

    id = Column(String(120), primary_key=True)  # e.g., 'doc_{id}_chunk_001'
    document_id = Column(String(36), ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    source_id = Column(String(100), ForeignKey("educational_sources.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chapter = Column(String(255), nullable=True)
    section = Column(String(255), nullable=True)
    page_number = Column(Integer, default=1, nullable=False)
    content = Column(Text, nullable=False)
    extracted_math = Column(JSON, default=list, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    embedding_id = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")


class QualityReport(Base):
    """Audit and data-quality validation report for knowledge base integrity."""

    __tablename__ = "knowledge_quality_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), nullable=True, index=True)
    source_id = Column(String(100), nullable=True, index=True)
    report_type = Column(String(50), nullable=False)  # ingestion_validation, audit, duplicate_check
    missing_text_warnings = Column(Integer, default=0, nullable=False)
    duplicate_chunks_count = Column(Integer, default=0, nullable=False)
    invalid_metadata_errors = Column(Integer, default=0, nullable=False)
    unsupported_format_errors = Column(Integer, default=0, nullable=False)
    status = Column(String(30), nullable=False)  # passed, flagged_warnings, failed
    details_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
