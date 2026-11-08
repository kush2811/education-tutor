"""Document extraction engine supporting PDF, DOCX, HTML, and Markdown/Text with structural preservation."""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from app.core.logging import logger
from app.services.knowledge_cleaner import content_cleaner


@dataclass
class ExtractedSection:
    """A structurally parsed segment of an educational document."""
    chapter: Optional[str] = None
    section: Optional[str] = None
    heading: Optional[str] = None
    page_number: int = 1
    text: str = ""
    tables: List[str] = field(default_factory=list)
    equations: List[str] = field(default_factory=list)


@dataclass
class ExtractedDocumentData:
    """Complete parsed representation of an ingested document."""
    title: str
    total_pages: int
    file_type: str
    metadata: Dict[str, Any]
    sections: List[ExtractedSection]
    raw_full_text: str


class DocumentExtractionEngine:
    """Extracts text, headings, paragraphs, tables, equations, and page numbers from academic documents."""

    def __init__(self):
        self.math_regex = re.compile(
            r'(\$\$.*?\$\$|\$[^\$\n]+\$|\\begin\{equation\}.*?\\end\{equation\})',
            re.DOTALL
        )

    def extract_equations(self, text: str) -> List[str]:
        """Isolate all inline and display LaTeX equations from text."""
        matches = self.math_regex.findall(text)
        return [m.strip() for m in matches if len(m.strip()) > 2]

    def extract_from_file(self, file_path: str, file_type: Optional[str] = None) -> ExtractedDocumentData:
        """Route to appropriate parser based on file extension or explicit type."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target document not found at: {file_path}")

        ext = file_type or os.path.splitext(file_path)[1].lower().lstrip(".")

        if ext == "pdf":
            return self._extract_pdf(file_path)
        elif ext in ["docx", "doc"]:
            return self._extract_docx(file_path)
        elif ext in ["html", "htm"]:
            return self._extract_html(file_path)
        elif ext in ["txt", "md", "markdown", "text"]:
            return self._extract_text(file_path)
        else:
            raise ValueError(f"Unsupported educational file format: '.{ext}'")

    def _extract_pdf(self, file_path: str) -> ExtractedDocumentData:
        """Extract text, tables, and page metadata from PDF using PyMuPDF."""
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz

        doc = fitz.open(file_path)
        total_pages = len(doc)
        doc_metadata = doc.metadata or {}
        title = doc_metadata.get("title") or os.path.splitext(os.path.basename(file_path))[0]

        sections: List[ExtractedSection] = []
        full_text_parts: List[str] = []
        current_chapter: Optional[str] = None
        current_section: Optional[str] = None

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1
            page_text = page.get_text("text") or ""
            cleaned_page_text = content_cleaner.clean_text(page_text)

            # Table extraction using PyMuPDF find_tables
            page_tables: List[str] = []
            try:
                tabs = page.find_tables()
                if tabs and len(tabs.tables) > 0:
                    for tab in tabs:
                        df = tab.extract()
                        if df and len(df) > 1:
                            header = df[0]
                            col_count = len(header)
                            md_rows = [
                                "| " + " | ".join(str(c or "").strip() for c in header) + " |",
                                "| " + " | ".join(["---"] * col_count) + " |"
                            ]
                            for row in df[1:]:
                                md_rows.append("| " + " | ".join(str(c or "").strip() for c in row) + " |")
                            page_tables.append("\n".join(md_rows))
            except Exception as e:
                logger.debug(f"PDF table parsing skipped for page {page_num}: {e}")

            # Heading and section heuristics
            lines = cleaned_page_text.splitlines()
            for line in lines[:5]:
                stripped = line.strip()
                if re.match(r'^(?:Chapter|Unit)\s+\d+[:\s\-]*(.+)?', stripped, re.IGNORECASE):
                    current_chapter = stripped
                elif re.match(r'^\d+\.\d+\s+[\w\s]{3,60}$', stripped):
                    current_section = stripped

            equations = self.extract_equations(cleaned_page_text)

            if cleaned_page_text.strip() or page_tables:
                sections.append(ExtractedSection(
                    chapter=current_chapter,
                    section=current_section,
                    heading=current_section or current_chapter,
                    page_number=page_num,
                    text=cleaned_page_text,
                    tables=page_tables,
                    equations=equations
                ))
                full_text_parts.append(cleaned_page_text)

        doc.close()
        return ExtractedDocumentData(
            title=title,
            total_pages=total_pages,
            file_type="pdf",
            metadata=doc_metadata,
            sections=sections,
            raw_full_text="\n\n".join(full_text_parts)
        )

    def _extract_docx(self, file_path: str) -> ExtractedDocumentData:
        """Extract headings, paragraphs, and tables from DOCX using python-docx."""
        import docx

        doc = docx.Document(file_path)
        title = os.path.splitext(os.path.basename(file_path))[0]
        sections: List[ExtractedSection] = []
        full_text_parts: List[str] = []

        current_chapter: Optional[str] = None
        current_section: Optional[str] = None
        current_heading: Optional[str] = None
        current_paragraphs: List[str] = []

        # Parse paragraphs
        for p in doc.paragraphs:
            text = content_cleaner.clean_text(p.text)
            if not text:
                continue

            style_name = p.style.name.lower() if p.style else ""
            if "heading 1" in style_name:
                # Flush existing buffer
                if current_paragraphs:
                    sec_text = "\n".join(current_paragraphs)
                    sections.append(ExtractedSection(
                        chapter=current_chapter,
                        section=current_section,
                        heading=current_heading,
                        page_number=1,
                        text=sec_text,
                        equations=self.extract_equations(sec_text)
                    ))
                    full_text_parts.append(sec_text)
                    current_paragraphs = []
                current_chapter = text
                current_heading = text
                current_paragraphs.append(text)
            elif "heading 2" in style_name or "heading 3" in style_name:
                if current_paragraphs:
                    sec_text = "\n".join(current_paragraphs)
                    sections.append(ExtractedSection(
                        chapter=current_chapter,
                        section=current_section,
                        heading=current_heading,
                        page_number=1,
                        text=sec_text,
                        equations=self.extract_equations(sec_text)
                    ))
                    full_text_parts.append(sec_text)
                    current_paragraphs = []
                current_section = text
                current_heading = text
                current_paragraphs.append(text)
            else:
                current_paragraphs.append(text)

        # Flush any remaining paragraphs
        if current_paragraphs:
            sec_text = "\n".join(current_paragraphs)
            sections.append(ExtractedSection(
                chapter=current_chapter,
                section=current_section,
                heading=current_heading,
                page_number=1,
                text=sec_text,
                equations=self.extract_equations(sec_text)
            ))
            full_text_parts.append(sec_text)

        # Parse tables
        doc_tables: List[str] = []
        for table in doc.tables:
            rows_data = []
            for row in table.rows:
                rows_data.append([c.text.strip() for c in row.cells])
            if rows_data:
                col_count = len(rows_data[0])
                md_rows = [
                    "| " + " | ".join(rows_data[0]) + " |",
                    "| " + " | ".join(["---"] * col_count) + " |"
                ]
                for r in rows_data[1:]:
                    md_rows.append("| " + " | ".join(r) + " |")
                doc_tables.append("\n".join(md_rows))

        if doc_tables and sections:
            sections[0].tables.extend(doc_tables)

        return ExtractedDocumentData(
            title=title,
            total_pages=1,
            file_type="docx",
            metadata={"source": file_path},
            sections=sections,
            raw_full_text="\n\n".join(full_text_parts)
        )

    def _extract_html(self, file_path: str) -> ExtractedDocumentData:
        """Extract structured content from HTML using BeautifulSoup."""
        from bs4 import BeautifulSoup

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else os.path.splitext(os.path.basename(file_path))[0]

        # Strip scripts, styles, navigations
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        sections: List[ExtractedSection] = []
        full_text_parts: List[str] = []
        current_heading: Optional[str] = None
        current_paragraphs: List[str] = []

        for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "table", "pre"]):
            tag_name = element.name.lower()
            if tag_name in ["h1", "h2", "h3", "h4"]:
                if current_paragraphs:
                    sec_text = "\n".join(current_paragraphs)
                    sections.append(ExtractedSection(
                        heading=current_heading,
                        page_number=1,
                        text=sec_text,
                        equations=self.extract_equations(sec_text)
                    ))
                    full_text_parts.append(sec_text)
                    current_paragraphs = []
                current_heading = content_cleaner.clean_text(element.get_text())
                if current_heading:
                    current_paragraphs.append(current_heading)
            elif tag_name == "table":
                # Convert HTML table to Markdown table
                rows = element.find_all("tr")
                if rows:
                    md_table_lines = []
                    header_cells = [c.get_text().strip() for c in rows[0].find_all(["th", "td"])]
                    if header_cells:
                        md_table_lines.append("| " + " | ".join(header_cells) + " |")
                        md_table_lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")
                        for row in rows[1:]:
                            cells = [c.get_text().strip() for c in row.find_all(["td", "th"])]
                            md_table_lines.append("| " + " | ".join(cells) + " |")
                        current_paragraphs.append("\n".join(md_table_lines))
            else:
                clean_p = content_cleaner.clean_text(element.get_text())
                if clean_p:
                    current_paragraphs.append(clean_p)

        if current_paragraphs:
            sec_text = "\n".join(current_paragraphs)
            sections.append(ExtractedSection(
                heading=current_heading,
                page_number=1,
                text=sec_text,
                equations=self.extract_equations(sec_text)
            ))
            full_text_parts.append(sec_text)

        return ExtractedDocumentData(
            title=title,
            total_pages=1,
            file_type="html",
            metadata={"source": file_path},
            sections=sections,
            raw_full_text="\n\n".join(full_text_parts)
        )

    def _extract_text(self, file_path: str) -> ExtractedDocumentData:
        """Extract sections from Markdown or plain text files."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()

        title = os.path.splitext(os.path.basename(file_path))[0]
        cleaned = content_cleaner.clean_text(raw_content)
        sections: List[ExtractedSection] = []

        current_heading: Optional[str] = None
        current_paragraphs: List[str] = []

        lines = cleaned.splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                # Heading in markdown
                if current_paragraphs:
                    sec_text = "\n".join(current_paragraphs)
                    sections.append(ExtractedSection(
                        heading=current_heading,
                        page_number=1,
                        text=sec_text,
                        equations=self.extract_equations(sec_text)
                    ))
                    current_paragraphs = []
                current_heading = stripped.lstrip("#").strip()
                if current_heading:
                    current_paragraphs.append(current_heading)
            elif stripped:
                current_paragraphs.append(stripped)

        if current_paragraphs:
            sec_text = "\n".join(current_paragraphs)
            sections.append(ExtractedSection(
                heading=current_heading,
                page_number=1,
                text=sec_text,
                equations=self.extract_equations(sec_text)
            ))

        return ExtractedDocumentData(
            title=title,
            total_pages=1,
            file_type="text",
            metadata={"source": file_path},
            sections=sections,
            raw_full_text=cleaned
        )


document_extractor = DocumentExtractionEngine()
