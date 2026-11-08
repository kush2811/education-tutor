"""DOCX processing service for structured paragraphs, headings, and tables."""

import io
import re
from typing import Dict, Any, List, Optional
from app.core.logging import logger
from app.schemas.unified_input import UnifiedQuestionPayload, SourceFileInfo, SourceReference

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class DOCXProcessor:
    """Extracts structured text, headings hierarchy, and table grids from Microsoft Word (.docx) files."""

    def process_docx(
        self,
        docx_bytes: bytes,
        filename: str,
        file_path: Optional[str] = None
    ) -> UnifiedQuestionPayload:
        """Parse Word document byte stream and extract structured content."""
        if not HAS_DOCX:
            raise RuntimeError("python-docx is required for DOCX processing.")

        doc = docx.Document(io.BytesIO(docx_bytes))
        
        extracted_sections: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        references: List[SourceReference] = []
        math_formulas: List[str] = []

        logger.info(f"Processing DOCX '{filename}' ({len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables)")

        current_heading = "Introduction"
        current_paragraphs: List[str] = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name if p.style else ""
            if "Heading" in style_name:
                if current_paragraphs:
                    extracted_sections.append({
                        "heading": current_heading,
                        "paragraphs": current_paragraphs
                    })
                    current_paragraphs = []
                current_heading = text
                references.append(SourceReference(
                    ref_type="page",
                    label=text,
                    excerpt=text[:100]
                ))
            else:
                current_paragraphs.append(text)
                full_text_parts.append(text)
                
                # Check for math formulas
                formulas = re.findall(r"\$([^\$]+)\$", text)
                math_formulas.extend(formulas)

        if current_paragraphs:
            extracted_sections.append({
                "heading": current_heading,
                "paragraphs": current_paragraphs
            })

        # Process tables
        extracted_tables = []
        for t_idx, table in enumerate(doc.tables):
            rows_data = []
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                rows_data.append(cells)
            if rows_data:
                extracted_tables.append({
                    "table_index": t_idx + 1,
                    "rows": rows_data
                })

        full_content = "\n\n".join(full_text_parts)
        primary_question = self._extract_question(full_content, filename)

        source_info = SourceFileInfo(
            file_name=filename,
            file_type="docx",
            file_size_bytes=len(docx_bytes),
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_path=file_path
        )

        return UnifiedQuestionPayload(
            input_type="docx",
            extracted_question=primary_question,
            extracted_context=full_content[:4000],
            math_expressions=list(set(math_formulas))[:10],
            source_file=source_info,
            references=references,
            confidence_score=0.98,
            metadata={
                "section_count": len(extracted_sections),
                "sections": extracted_sections[:10],
                "table_count": len(extracted_tables),
                "extracted_tables": extracted_tables[:5]
            }
        )

    def _extract_question(self, text: str, filename: str) -> str:
        """Find the core question inside the docx content."""
        q_sentences = [s.strip() for s in text.split("\n") if "?" in s]
        if q_sentences:
            return q_sentences[0][:300]
        first_para = text.split("\n\n")[0].strip() if text else ""
        if first_para:
            return f"Problem from worksheet: '{first_para[:250]}...'"
        return f"Solve and explain worksheet questions from {filename}"


docx_processor = DOCXProcessor()
