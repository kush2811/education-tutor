"""PDF processing service for structural text, page references, tables, and metadata."""

import os
import re
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from app.schemas.unified_input import UnifiedQuestionPayload, SourceFileInfo, SourceReference

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class PDFProcessor:
    """Extracts structured text, page-indexed citations, tables, and document metadata from educational PDFs."""

    def process_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        file_path: Optional[str] = None
    ) -> UnifiedQuestionPayload:
        """Parse PDF byte stream, extract page-by-page text, tables, and construct a UnifiedQuestionPayload."""
        if not HAS_PYMUPDF:
            raise RuntimeError("PyMuPDF (fitz) is required for PDF processing.")

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        meta = doc.metadata or {}

        doc_title = meta.get("title") or filename
        author = meta.get("author") or "Academic Source"

        pages_text: List[str] = []
        references: List[SourceReference] = []
        all_tables: List[Dict[str, Any]] = []
        math_formulas: List[str] = []

        logger.info(f"Processing PDF '{filename}' ({total_pages} pages, {len(pdf_bytes)} bytes)")

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)
            text = page.get_text("text").strip()
            pages_text.append(text)

            # Table extraction if supported
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    for t_idx, t in enumerate(tables.tables):
                        extracted_table = t.extract()
                        if extracted_table:
                            all_tables.append({
                                "page": page_num,
                                "table_index": t_idx + 1,
                                "rows": extracted_table
                            })
            except Exception as tbl_err:
                logger.debug(f"Table extraction skipped for page {page_num}: {tbl_err}")

            # Capture page reference anchor for citations
            first_sentence = text.split("\n")[0][:120] if text else f"Page {page_num} content"
            references.append(SourceReference(
                ref_type="page",
                page_number=page_num,
                label=f"Page {page_num}",
                excerpt=first_sentence
            ))

            # Extract any embedded $...$ math expressions
            found_formulas = re.findall(r"\$([^\$]+)\$", text)
            math_formulas.extend(found_formulas[:10])  # limit per page

        doc.close()

        # Combine text for question formulation
        full_text = "\n\n".join(pages_text)

        # Formulate primary question from the document
        extracted_question = self._extract_primary_question(full_text, filename)

        source_info = SourceFileInfo(
            file_name=filename,
            file_type="pdf",
            file_size_bytes=len(pdf_bytes),
            mime_type="application/pdf",
            file_path=file_path
        )

        return UnifiedQuestionPayload(
            input_type="pdf",
            extracted_question=extracted_question,
            extracted_context=full_text[:4000],  # first 4000 chars of context
            math_expressions=list(set(math_formulas))[:15],
            source_file=source_info,
            references=references,
            confidence_score=0.98,
            metadata={
                "total_pages": total_pages,
                "document_title": doc_title,
                "author": author,
                "table_count": len(all_tables),
                "extracted_tables": all_tables[:5]
            }
        )

    def _extract_primary_question(self, text: str, filename: str) -> str:
        """Find the prominent question in the PDF (e.g. Question 1, Problem, or header)."""
        # Look for explicit problem markers like "Problem 1:", "Q.1", "Question:"
        match = re.search(r"(?:Problem|Question|Q\.?)\s*\d*[:\.\)]\s*(.*?)(?=\n\s*(?:Problem|Question|Q\.?|\d+[\.\)])|\n\n|$)", text, re.DOTALL | re.IGNORECASE)
        if match:
            q = match.group(0).strip()
            if len(q) > 20:
                return q[:350]

        # Look for sentences ending with '?'
        q_sentences = [s.strip() for s in text.split("\n") if "?" in s]
        if q_sentences:
            return q_sentences[0][:300]

        # Default fallback
        first_para = text.split("\n\n")[0].strip() if text else ""
        if first_para:
            return f"Review and analyze this worksheet: '{first_para[:250]}...'"
        return f"Analyze and provide Socratic guidance for the uploaded PDF: {filename}"


pdf_processor = PDFProcessor()

