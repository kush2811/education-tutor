"""Data quality auditing, anomaly detection, and validation reporting for educational knowledge bases."""

from typing import List, Dict, Any, Tuple
from app.services.knowledge_extractor import ExtractedDocumentData
from app.services.educational_chunker import EducationalChunk
from app.models.knowledge import QualityReport


class DataQualityAuditor:
    """Audits educational document ingestion and chunking to safeguard curriculum accuracy."""

    def audit_document_ingestion(
        self,
        extracted: ExtractedDocumentData,
        chunks: List[EducationalChunk],
        metadata: Dict[str, Any],
        document_id: str,
        source_id: str
    ) -> Dict[str, Any]:
        """Perform a comprehensive quality check on extracted content and chunks."""
        missing_text_warnings = 0
        duplicate_chunks_count = 0
        invalid_metadata_errors = 0
        unsupported_format_errors = 0
        issues: List[str] = []

        # 1. Extraction Failure Check
        if not extracted.sections or not extracted.raw_full_text.strip():
            issues.append("Extraction failure: No text sections were extracted from the document.")

        # 2. Missing text check in chunks
        for chk in chunks:
            if len(chk.content.strip()) < 50:
                missing_text_warnings += 1
                issues.append(f"Chunk '{chk.chunk_id}' has suspiciously short content ({len(chk.content.strip())} characters).")

        # 3. Duplicate chunks check (within document)
        seen_hashes = set()
        for chk in chunks:
            if chk.sha256_hash in seen_hashes:
                duplicate_chunks_count += 1
                issues.append(f"Duplicate chunk detected: '{chk.chunk_id}' shares an identical SHA-256 hash.")
            seen_hashes.add(chk.sha256_hash)

        # 4. Metadata validation
        required_meta_keys = ["title", "subject", "academic_level", "source_id"]
        for key in required_meta_keys:
            val = metadata.get(key)
            if not val or not str(val).strip():
                invalid_metadata_errors += 1
                issues.append(f"Missing required metadata field: '{key}'.")

        # 5. Unsupported format check
        supported_formats = ["pdf", "docx", "doc", "html", "htm", "txt", "md"]
        if extracted.file_type.lower() not in supported_formats:
            unsupported_format_errors += 1
            issues.append(f"Unsupported document format: '{extracted.file_type}'.")

        # Determine overall status
        if unsupported_format_errors > 0 or not extracted.sections:
            status = "failed"
        elif missing_text_warnings > 0 or duplicate_chunks_count > 0 or invalid_metadata_errors > 0:
            status = "flagged_warnings"
        else:
            status = "passed"

        return {
            "document_id": document_id,
            "source_id": source_id,
            "report_type": "ingestion_validation",
            "missing_text_warnings": missing_text_warnings,
            "duplicate_chunks_count": duplicate_chunks_count,
            "invalid_metadata_errors": invalid_metadata_errors,
            "unsupported_format_errors": unsupported_format_errors,
            "status": status,
            "issues": issues,
            "total_chunks_inspected": len(chunks),
            "total_pages_inspected": extracted.total_pages
        }


data_quality_auditor = DataQualityAuditor()
