"""Document parser service for extracting text, tables, and images from PDFs and DOCX files."""

import os
from typing import Dict, Any, List
from app.core.logging import logger

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


class DocumentParserService:
    """Extracts layout-aware structural text, page numbers, and figures from educational documents."""

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text, page count, and structural metadata from a PDF file."""
        if not HAS_PYMUPDF:
            logger.warning("PyMuPDF (fitz) is not installed. Returning basic metadata.")
            return {"file_path": file_path, "pages": [], "total_pages": 0}

        pages_data = []
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                pages_data.append({
                    "page_number": page_num + 1,
                    "text": text.strip(),
                    "char_count": len(text)
                })
            doc.close()
            return {
                "file_path": file_path,
                "total_pages": total_pages,
                "pages": pages_data,
                "status": "parsed"
            }
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise


doc_parser_service = DocumentParserService()

