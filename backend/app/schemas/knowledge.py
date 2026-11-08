"""Pydantic schemas for educational knowledge base, sources, documents, and chunks."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class EducationalSourceBase(BaseModel):
    """Base schema for an educational source."""
    source_name: str = Field(..., min_length=3, max_length=255, description="Official name of the resource")
    source_url: str = Field(..., max_length=500, description="Canonical URL")
    subject: str = Field(..., min_length=2, max_length=100, description="Subject domain, e.g. Mathematics, Physics")
    academic_level: str = Field(..., min_length=2, max_length=100, description="Target level, e.g. Grade 10, Undergraduate")
    license_type: str = Field(..., min_length=3, max_length=255, description="Legal usage license, e.g. CC BY 4.0, Fair Dealing")
    source_authority: str = Field(..., min_length=2, max_length=255, description="Authoritative publisher or institution")
    authority_category: str = Field(
        ...,
        description="One of: ncert, gov_portal, university, oer, programming_docs, research"
    )
    description: Optional[str] = Field(None, description="Overview of the curriculum or source materials")


class EducationalSourceCreate(EducationalSourceBase):
    """Payload to register a new educational source."""
    id: Optional[str] = Field(None, max_length=100, description="Custom unique slug or generated UUID")


class EducationalSourceResponse(EducationalSourceBase):
    """Full representation of a registered educational source."""
    id: str
    collection_date: datetime
    last_updated_date: datetime
    is_active: bool
    document_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    """Educational chunk with citation and formula metadata."""
    id: str
    chunk_index: int
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: int
    content: str
    extracted_math: List[str] = Field(default_factory=list)
    token_count: int
    sha256_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeDocumentResponse(BaseModel):
    """Summary of an ingested educational document."""
    id: str
    source_id: str
    title: str
    file_type: str
    file_size: int
    sha256_hash: str
    version: int
    total_pages: int
    total_chunks: int
    status: str
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeDocumentDetailResponse(KnowledgeDocumentResponse):
    """Detailed document response including sample or all chunks."""
    source: Optional[EducationalSourceResponse] = None
    chunks: List[DocumentChunkResponse] = Field(default_factory=list)


class DocumentIngestResponse(BaseModel):
    """Response returned upon successful document ingestion and indexing."""
    document_id: str
    source_id: str
    title: str
    version: int
    total_pages: int
    chunks_created: int
    sha256_hash: str
    status: str
    quality_status: str
    message: str


class QualityReportResponse(BaseModel):
    """Data quality and validation audit report."""
    id: str
    document_id: Optional[str] = None
    source_id: Optional[str] = None
    report_type: str
    missing_text_warnings: int
    duplicate_chunks_count: int
    invalid_metadata_errors: int
    unsupported_format_errors: int
    status: str  # passed, flagged_warnings, failed
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeQueryRequest(BaseModel):
    """Search inquiry against the educational curriculum vector store."""
    query: str = Field(..., min_length=2, description="Student question, math concept, or theorem name")
    subject: Optional[str] = Field(None, description="Filter by subject domain (e.g. Mathematics)")
    academic_level: Optional[str] = Field(None, description="Filter by academic grade or level")
    source_id: Optional[str] = Field(None, description="Constrain search to a specific registered source")
    top_k: int = Field(default=5, ge=1, le=25, description="Number of curriculum excerpts to retrieve")


class KnowledgeQueryResultItem(BaseModel):
    """Retrieved curriculum excerpt with citation grounding."""
    chunk_id: str
    document_id: str
    source_id: str
    source_name: str
    authority: str
    license_type: str
    subject: str
    academic_level: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: int
    content: str
    extracted_math: List[str] = Field(default_factory=list)
    similarity_score: float
    citation: str = Field(..., description="Official verifiable citation string")


class KnowledgeQueryResponse(BaseModel):
    """Aggregated semantic search results from the educational knowledge base."""
    query: str
    total_matches: int
    results: List[KnowledgeQueryResultItem]

