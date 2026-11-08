"""Citation validation service: verifies existence, document matching, page numbers, and URLs."""

import re
from typing import List, Tuple, Optional
from urllib.parse import urlparse

from app.schemas.rag import RAGCitation, RetrievedChunkItem
from app.schemas.validation import CitationCheckStatus, CitationValidationItem


class CitationValidator:
    """Audits citation references in AI answers against actual retrieved curriculum context."""

    def __init__(self):
        # Matches patterns like [1], [2], [1, 2], [10]
        self._citation_pattern = re.compile(r'\[(\d+)\]')

    def validate_citations(
        self,
        answer: str,
        citations: List[RAGCitation],
        retrieved_chunks: Optional[List[RetrievedChunkItem]] = None
    ) -> Tuple[List[CitationValidationItem], str, List[str]]:
        """
        Validate all citation markers in the answer text.
        
        Returns:
            - List of CitationValidationItem audits
            - Sanitized answer text (phantom citations flagged/annotated)
            - List of warning messages
        """
        audit_items: List[CitationValidationItem] = []
        warnings: List[str] = []
        sanitized_text = answer

        # 1. Extract all [N] references in the answer
        found_indices = [int(m) for m in self._citation_pattern.findall(answer)]
        unique_indices = sorted(list(set(found_indices)))

        # Build lookup maps for fast verification
        citation_map = {}
        for c in citations:
            # Extract number from label e.g. "[1]" -> 1
            lbl_match = re.search(r'\d+', c.citation_label)
            if lbl_match:
                citation_map[int(lbl_match.group(0))] = c

        chunk_map = {idx + 1: ch for idx, ch in enumerate(retrieved_chunks or [])}

        # 2. Audit each referenced citation index
        for idx in unique_indices:
            label = f"[{idx}]"

            # Check: Does index exist in available citations?
            if idx not in citation_map and idx not in chunk_map:
                audit_items.append(
                    CitationValidationItem(
                        citation_label=label,
                        status=CitationCheckStatus.PHANTOM_INDEX,
                        details=f"Citation marker {label} does not correspond to any retrieved curriculum source (Total available: {len(citations)})."
                    )
                )
                warnings.append(f"Phantom citation detected: {label} has no matching curriculum reference.")
                # Annotate in sanitized text
                sanitized_text = re.sub(
                    rf'\[{idx}\]',
                    f"[{idx} (Unverified Citation)]",
                    sanitized_text
                )
                continue

            # Citation object is present
            cit_obj = citation_map.get(idx)
            chunk_obj = chunk_map.get(idx)

            source_id = cit_obj.source_id if cit_obj else (chunk_obj.source_id if chunk_obj else "unknown")
            source_name = cit_obj.source_name if cit_obj else (chunk_obj.source_name if chunk_obj else "unknown")
            page_num = cit_obj.page_number if cit_obj else (chunk_obj.page_number if chunk_obj else 1)
            source_url = cit_obj.source_url if cit_obj else (chunk_obj.source_url if chunk_obj else "")

            # Check URL validity
            url_valid, url_err = self._is_valid_url(source_url)
            if not url_valid:
                audit_items.append(
                    CitationValidationItem(
                        citation_label=label,
                        status=CitationCheckStatus.INVALID_URL,
                        source_id=source_id,
                        source_name=source_name,
                        page_number=page_num,
                        source_url=source_url,
                        details=f"Citation {label} provides an invalid or hallucinated URL: '{source_url}' ({url_err})."
                    )
                )
                warnings.append(f"Invalid citation URL in {label}: {source_url}")
                continue

            # Check Page Number Validity
            if page_num < 1:
                audit_items.append(
                    CitationValidationItem(
                        citation_label=label,
                        status=CitationCheckStatus.INVALID_PAGE,
                        source_id=source_id,
                        source_name=source_name,
                        page_number=page_num,
                        source_url=source_url,
                        details=f"Citation {label} has an impossible page number ({page_num})."
                    )
                )
                warnings.append(f"Invalid page reference in {label}: page {page_num}")
                continue

            # Check document alignment if both chunk and citation exist
            if cit_obj and chunk_obj and cit_obj.source_id != chunk_obj.source_id:
                audit_items.append(
                    CitationValidationItem(
                        citation_label=label,
                        status=CitationCheckStatus.MISMATCHED_DOCUMENT,
                        source_id=source_id,
                        source_name=source_name,
                        page_number=page_num,
                        source_url=source_url,
                        details=(
                            f"Citation {label} refers to source '{cit_obj.source_id}' "
                            f"but underlying retrieved chunk {idx} belongs to '{chunk_obj.source_id}'."
                        )
                    )
                )
                warnings.append(f"Mismatched document metadata in citation {label}.")
                continue

            # Passed all checks
            audit_items.append(
                CitationValidationItem(
                    citation_label=label,
                    status=CitationCheckStatus.VALID,
                    source_id=source_id,
                    source_name=source_name,
                    page_number=page_num,
                    source_url=source_url,
                    details=f"Citation {label} verified: Grounded in '{source_name}', page {page_num}."
                )
            )

        # 3. Check for unused citations
        # If retrieved context has citations but the answer didn't cite them, note for diagnostic audit
        unused_citations = [f"[{k}]" for k in citation_map.keys() if k not in unique_indices]
        if unused_citations and unique_indices:
            warnings.append(f"Retrieved citations {', '.join(unused_citations)} were not cited in the answer body.")

        return audit_items, sanitized_text, warnings

    def _is_valid_url(self, url: Optional[str]) -> Tuple[bool, str]:
        """Validate URL structure and canonical schemes."""
        if not url:
            return False, "Missing URL"
        url = url.strip()
        if " " in url:
            return False, "Contains whitespace"
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False, f"Unsupported scheme: '{parsed.scheme}'"
            if not parsed.netloc:
                return False, "Missing network location domain"
            if "." not in parsed.netloc:
                return False, f"Invalid domain: '{parsed.netloc}'"
            return True, "Valid"
        except Exception as e:
            return False, str(e)


citation_validator = CitationValidator()
