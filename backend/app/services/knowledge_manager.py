"""Knowledge base manager orchestrating ingestion, versioning, duplicate detection, re-indexing, and search."""

import os
import uuid
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.knowledge import (
    EducationalSource,
    KnowledgeDocument,
    DocumentChunk,
    QualityReport,
)
from app.schemas.knowledge import (
    DocumentIngestResponse,
    KnowledgeQueryResponse,
    KnowledgeQueryResultItem,
)
from app.services.knowledge_extractor import document_extractor
from app.services.educational_chunker import educational_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.data_quality import data_quality_auditor


class KnowledgeBaseManager:
    """Master controller for the educational knowledge base."""

    @staticmethod
    def compute_file_sha256(file_path: str) -> str:
        """Compute SHA-256 checksum of a file on disk."""
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                sha.update(block)
        return sha.hexdigest()

    def add_document(
        self,
        source_id: str,
        file_path: str,
        db: Session,
        title: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentIngestResponse:
        """Ingest, clean, chunk, embed, and index an educational document."""
        source = db.query(EducationalSource).filter(EducationalSource.id == source_id).first()
        if not source:
            raise ValueError(f"Educational source '{source_id}' is not registered.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_hash = self.compute_file_sha256(file_path)
        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")

        # Duplicate document check
        existing_doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.sha256_hash == file_hash,
            KnowledgeDocument.source_id == source_id
        ).first()
        if existing_doc:
            logger.info(f"Duplicate document detected (ID: {existing_doc.id}, Hash: {file_hash}). Returning existing.")
            return DocumentIngestResponse(
                document_id=existing_doc.id,
                source_id=source.id,
                title=existing_doc.title,
                version=existing_doc.version,
                total_pages=existing_doc.total_pages,
                chunks_created=existing_doc.total_chunks,
                sha256_hash=existing_doc.sha256_hash,
                status="duplicate_existing",
                quality_status="passed",
                message=f"Document already indexed under ID {existing_doc.id} (Version {existing_doc.version})."
            )

        # 1. Extract structured sections
        extracted = document_extractor.extract_from_file(file_path, file_type=ext)
        doc_title = title or extracted.title or os.path.basename(file_path)
        doc_id = str(uuid.uuid4())

        # Combine metadata
        combined_meta = {
            "title": doc_title,
            "source_id": source.id,
            "source_name": source.source_name,
            "subject": source.subject,
            "academic_level": source.academic_level,
            "source_authority": source.source_authority,
            "license_type": source.license_type,
            "original_filename": os.path.basename(file_path),
            "file_size": file_size,
        }
        if custom_metadata:
            combined_meta.update(custom_metadata)

        # 2. Educational concept-aware chunking
        chunks = educational_chunker.chunk_document(
            extracted=extracted,
            document_id=doc_id,
            source_id=source.id,
            source_name=source.source_name,
            subject=source.subject,
            academic_level=source.academic_level
        )

        # 3. Data Quality Audit
        quality_result = data_quality_auditor.audit_document_ingestion(
            extracted=extracted,
            chunks=chunks,
            metadata=combined_meta,
            document_id=doc_id,
            source_id=source.id
        )

        # 4. Generate Embeddings
        chunk_contents = [c.content for c in chunks]
        embeddings = embedding_service.embed_batch(chunk_contents)

        # 5. Store in ChromaDB Vector Store
        vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
            additional_metadata={
                "source_authority": source.source_authority,
                "license_type": source.license_type
            }
        )

        # 6. Record in Database
        doc_record = KnowledgeDocument(
            id=doc_id,
            source_id=source.id,
            title=doc_title,
            file_path=file_path,
            file_type=ext,
            file_size=file_size,
            sha256_hash=file_hash,
            version=1,
            total_pages=extracted.total_pages,
            total_chunks=len(chunks),
            status="indexed",
            metadata_json=combined_meta
        )
        db.add(doc_record)

        for chk in chunks:
            chunk_record = DocumentChunk(
                id=chk.chunk_id,
                document_id=doc_id,
                source_id=source.id,
                chunk_index=chk.chunk_index,
                chapter=chk.chapter,
                section=chk.section,
                page_number=chk.page_number,
                content=chk.content,
                extracted_math=chk.extracted_math,
                token_count=chk.token_count,
                sha256_hash=chk.sha256_hash,
                embedding_id=chk.chunk_id
            )
            db.add(chunk_record)

        # Record Quality Report
        q_report = QualityReport(
            document_id=doc_id,
            source_id=source.id,
            report_type="ingestion_validation",
            missing_text_warnings=quality_result["missing_text_warnings"],
            duplicate_chunks_count=quality_result["duplicate_chunks_count"],
            invalid_metadata_errors=quality_result["invalid_metadata_errors"],
            unsupported_format_errors=quality_result["unsupported_format_errors"],
            status=quality_result["status"],
            details_json=quality_result
        )
        db.add(q_report)

        # Update source document count
        source.document_count = (source.document_count or 0) + 1
        db.commit()

        logger.info(f"Ingested educational document '{doc_title}' ({len(chunks)} chunks, quality: {quality_result['status']}).")
        return DocumentIngestResponse(
            document_id=doc_id,
            source_id=source.id,
            title=doc_title,
            version=1,
            total_pages=extracted.total_pages,
            chunks_created=len(chunks),
            sha256_hash=file_hash,
            status="indexed",
            quality_status=quality_result["status"],
            message=f"Document successfully indexed into {len(chunks)} curriculum chunks."
        )

    def update_document(
        self,
        document_id: str,
        new_file_path: str,
        db: Session
    ) -> DocumentIngestResponse:
        """Update an existing educational document and re-index updated chunks with version increment."""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not doc:
            raise ValueError(f"Knowledge document '{document_id}' not found.")

        source = doc.source

        # Remove existing chunks from ChromaDB
        vector_store.delete_document(document_id)

        # Remove existing chunks from SQLite
        db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

        # Compute new file hash
        file_hash = self.compute_file_sha256(new_file_path)
        file_size = os.path.getsize(new_file_path)
        ext = os.path.splitext(new_file_path)[1].lower().lstrip(".")

        # Extract, chunk, embed
        extracted = document_extractor.extract_from_file(new_file_path, file_type=ext)
        new_version = doc.version + 1

        chunks = educational_chunker.chunk_document(
            extracted=extracted,
            document_id=document_id,
            source_id=source.id,
            source_name=source.source_name,
            subject=source.subject,
            academic_level=source.academic_level
        )

        quality_result = data_quality_auditor.audit_document_ingestion(
            extracted=extracted,
            chunks=chunks,
            metadata=doc.metadata_json,
            document_id=document_id,
            source_id=source.id
        )

        embeddings = embedding_service.embed_batch([c.content for c in chunks])
        vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
            additional_metadata={
                "source_authority": source.source_authority,
                "license_type": source.license_type
            }
        )

        # Update document record
        doc.file_path = new_file_path
        doc.file_size = file_size
        doc.sha256_hash = file_hash
        doc.version = new_version
        doc.total_pages = extracted.total_pages
        doc.total_chunks = len(chunks)
        doc.updated_at = datetime.utcnow()

        for chk in chunks:
            chunk_record = DocumentChunk(
                id=chk.chunk_id,
                document_id=document_id,
                source_id=source.id,
                chunk_index=chk.chunk_index,
                chapter=chk.chapter,
                section=chk.section,
                page_number=chk.page_number,
                content=chk.content,
                extracted_math=chk.extracted_math,
                token_count=chk.token_count,
                sha256_hash=chk.sha256_hash,
                embedding_id=chk.chunk_id
            )
            db.add(chunk_record)

        db.commit()
        logger.info(f"Updated document '{doc.title}' to version {new_version} ({len(chunks)} chunks).")

        return DocumentIngestResponse(
            document_id=document_id,
            source_id=source.id,
            title=doc.title,
            version=new_version,
            total_pages=extracted.total_pages,
            chunks_created=len(chunks),
            sha256_hash=file_hash,
            status="updated",
            quality_status=quality_result["status"],
            message=f"Document successfully updated to version {new_version} with {len(chunks)} chunks."
        )

    def remove_document(self, document_id: str, db: Session) -> bool:
        """Purge an educational document, its chunks, and its vector embeddings."""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not doc:
            return False

        source = doc.source
        # Purge from ChromaDB
        vector_store.delete_document(document_id)

        # Purge from database
        db.delete(doc)
        if source and source.document_count > 0:
            source.document_count -= 1

        db.commit()
        logger.info(f"Purged document '{document_id}' and all associated vector chunks.")
        return True

    def reindex_document(self, document_id: str, db: Session) -> DocumentIngestResponse:
        """Re-extract and re-embed an existing document from disk."""
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
        if not doc:
            raise ValueError(f"Knowledge document '{document_id}' not found.")
        return self.update_document(document_id=document_id, new_file_path=doc.file_path, db=db)

    def search_curriculum(
        self,
        query: str,
        db: Session,
        subject: Optional[str] = None,
        academic_level: Optional[str] = None,
        source_id: Optional[str] = None,
        top_k: int = 5
    ) -> KnowledgeQueryResponse:
        """Perform semantic search against indexed curriculum chunks with verified citation generation."""
        query_vec = embedding_service.embed_text(query)

        where_filter: Dict[str, Any] = {}
        if subject:
            where_filter["subject"] = subject
        if academic_level:
            where_filter["academic_level"] = academic_level
        if source_id:
            where_filter["source_id"] = source_id

        filter_arg = where_filter if where_filter else None
        matches = vector_store.query(
            query_embedding=query_vec,
            top_k=top_k,
            where_filter=filter_arg
        )

        results: List[KnowledgeQueryResultItem] = []
        for m in matches:
            meta = m["metadata"]
            # Look up math expressions if stored
            chunk_rec = db.query(DocumentChunk).filter(DocumentChunk.id == m["chunk_id"]).first()
            math_exprs = chunk_rec.extracted_math if chunk_rec and chunk_rec.extracted_math else []

            # Format verifiable academic citation
            source_title = meta.get("source_name") or "Curriculum Source"
            chapter = meta.get("chapter") or "Chapter"
            section = meta.get("section") or ""
            page = meta.get("page_number") or 1
            authority = meta.get("source_authority") or "Educational Authority"
            license_str = meta.get("license_type") or "Educational Use"

            citation_parts = [source_title]
            if chapter:
                citation_parts.append(chapter)
            if section:
                citation_parts.append(section)
            citation_parts.append(f"Page {page}")
            citation_parts.append(f"({authority})")
            citation_str = ", ".join(citation_parts)

            results.append(KnowledgeQueryResultItem(
                chunk_id=m["chunk_id"],
                document_id=meta.get("document_id", ""),
                source_id=meta.get("source_id", ""),
                source_name=source_title,
                authority=authority,
                license_type=license_str,
                subject=meta.get("subject", ""),
                academic_level=meta.get("academic_level", ""),
                chapter=meta.get("chapter"),
                section=meta.get("section"),
                page_number=int(page),
                content=m["content"],
                extracted_math=math_exprs,
                similarity_score=round(float(m["similarity"]), 4),
                citation=citation_str
            ))

        return KnowledgeQueryResponse(
            query=query,
            total_matches=len(results),
            results=results
        )


knowledge_manager = KnowledgeBaseManager()
