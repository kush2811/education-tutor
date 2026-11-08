"""Text cleaning, duplicate removal, boilerplate filtering, and metadata validation for educational documents."""

import re
import hashlib
from typing import Tuple, List, Dict, Any, Set


class EducationalContentCleaner:
    """Cleans educational texts, eliminates headers/footers, strips duplicates, and standardizes math."""

    # Common educational textbook boilerplate and running header/footer patterns
    BOILERPLATE_PATTERNS = [
        re.compile(r"^(?:Page\s+\d+\s*(?:of\s*\d+)?|\d+\s*(?:of\s*\d+)?)$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^(?:NCERT\s+not\s+to\s+be\s+republished|Not\s+to\s+be\s+republished)$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^(?:Downloaded\s+from\s+https?://\S+|Source:\s*https?://\S+)$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^(?:All\s+rights\s+reserved\.?|Copyright\s+©\s*\d{4}.*)$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^(?:Confidential\s+-\s+Internal\s+Use\s+Only)$", re.IGNORECASE | re.MULTILINE),
    ]

    UNICODE_REPLACEMENTS = {
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u2013": "-",  # En-dash
        "\u2014": " -- ",  # Em-dash
        "\u2026": "...",  # Ellipsis
        "\u00a0": " ",  # Non-breaking space
        "\ufeff": "",   # Zero-width no-break space (BOM)
    }

    def clean_text(self, text: str) -> str:
        """Clean raw extracted document text into standardized educational prose."""
        if not text:
            return ""

        # 1. Unicode standardization
        cleaned = text
        for u_char, repl in self.UNICODE_REPLACEMENTS.items():
            cleaned = cleaned.replace(u_char, repl)

        # 2. LaTeX bracket delimiter normalization
        cleaned = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'\\\((.*?)\\\)', r'$\1$', cleaned, flags=re.DOTALL)

        # 3. Strip known recurring boilerplate lines
        for pattern in self.BOILERPLATE_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # 4. Remove duplicate lines/paragraphs and normalize whitespace
        lines = cleaned.splitlines()
        deduped_lines: List[str] = []
        seen_line_hashes: Set[str] = set()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                deduped_lines.append("")
                continue

            # Compute short hash for duplicate detection on meaningful content lines (> 20 chars)
            if len(stripped) > 20:
                line_hash = hashlib.md5(stripped.lower().encode("utf-8")).hexdigest()
                # Check if this exact line occurred immediately before or repeatedly
                if deduped_lines and deduped_lines[-1].strip() == stripped:
                    continue  # Skip consecutive duplicate line
                # Keep tracking line
                seen_line_hashes.add(line_hash)

            deduped_lines.append(stripped)

        # 5. Condense excessive blank lines (max 2 consecutive newlines)
        rejoined = "\n".join(deduped_lines)
        rejoined = re.sub(r'\n{3,}', '\n\n', rejoined)

        return rejoined.strip()

    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate educational document metadata against data quality criteria."""
        errors: List[str] = []

        if not metadata.get("title") or len(str(metadata["title"]).strip()) < 3:
            errors.append("Document 'title' is missing or too short (minimum 3 characters).")

        if not metadata.get("source_id"):
            errors.append("Document 'source_id' is required for academic attribution.")

        if not metadata.get("subject"):
            errors.append("Document 'subject' domain is required.")

        if not metadata.get("academic_level"):
            errors.append("Document 'academic_level' is required.")

        return len(errors) == 0, errors


content_cleaner = EducationalContentCleaner()
