"""Concept-aware educational chunking engine preserving pedagogical coherence, formulas, and citations."""

import re
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from app.services.knowledge_extractor import ExtractedDocumentData, ExtractedSection


@dataclass
class EducationalChunk:
    """A pedagogically coherent text chunk with academic attribution metadata."""
    chunk_id: str
    document_id: str
    source_id: str
    chunk_index: int
    chapter: Optional[str]
    section: Optional[str]
    page_number: int
    content: str
    extracted_math: List[str] = field(default_factory=list)
    token_count: int = 0
    sha256_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class EducationalChunkingEngine:
    """Splits academic text along concept, sentence, and section boundaries without breaking math."""

    def __init__(self, target_chars: int = 1800, overlap_chars: int = 250):
        self.target_chars = target_chars
        self.overlap_chars = overlap_chars
        self.math_regex = re.compile(
            r'(\$\$.*?\$\$|\$[^\$\n]+\$|\\begin\{equation\}.*?\\end\{equation\})',
            re.DOTALL
        )

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while guarding decimal numbers (e.g. 3.14) and formulas."""
        # Temporarily protect math blocks
        math_blocks = []
        def _replace_math(match):
            placeholder = f"__MATH_BLOCK_{len(math_blocks)}__"
            math_blocks.append(match.group(0))
            return placeholder

        protected = self.math_regex.sub(_replace_math, text)

        # Split on sentence boundaries
        raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'\(\[])', protected)

        # Restore math blocks
        restored_sentences = []
        for s in raw_sentences:
            s_clean = s.strip()
            for idx, block in enumerate(math_blocks):
                placeholder = f"__MATH_BLOCK_{idx}__"
                if placeholder in s_clean:
                    s_clean = s_clean.replace(placeholder, block)
            if s_clean:
                restored_sentences.append(s_clean)

        return restored_sentences

    def chunk_document(
        self,
        extracted: ExtractedDocumentData,
        document_id: str,
        source_id: str,
        source_name: str,
        subject: str,
        academic_level: str
    ) -> List[EducationalChunk]:
        """Create structured concept-aware chunks across all sections of a document."""
        chunks: List[EducationalChunk] = []
        chunk_idx = 1

        for sec in extracted.sections:
            sec_text = sec.text.strip()
            if not sec_text and not sec.tables:
                continue

            # Append any extracted tables to section text as markdown blocks
            if sec.tables:
                tables_block = "\n\n" + "\n\n".join(sec.tables)
                full_sec_content = (sec_text + tables_block).strip()
            else:
                full_sec_content = sec_text

            sentences = self._split_into_sentences(full_sec_content)
            current_chunk_sentences: List[str] = []
            current_len = 0

            for sentence in sentences:
                sentence_len = len(sentence)
                if current_len + sentence_len > self.target_chars and current_chunk_sentences:
                    # Finalize current chunk
                    chunk_text = " ".join(current_chunk_sentences).strip()
                    math_found = [m.strip() for m in self.math_regex.findall(chunk_text) if len(m.strip()) > 2]
                    chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                    approx_tokens = max(1, len(chunk_text) // 4)

                    chunk_obj = EducationalChunk(
                        chunk_id=f"{document_id}_chk_{chunk_idx:03d}",
                        document_id=document_id,
                        source_id=source_id,
                        chunk_index=chunk_idx,
                        chapter=sec.chapter,
                        section=sec.section or sec.heading,
                        page_number=sec.page_number,
                        content=chunk_text,
                        extracted_math=math_found,
                        token_count=approx_tokens,
                        sha256_hash=chunk_hash,
                        metadata={
                            "document_id": document_id,
                            "document_title": extracted.title,
                            "source_id": source_id,
                            "source_name": source_name,
                            "subject": subject,
                            "academic_level": academic_level,
                            "chapter": sec.chapter or "",
                            "section": sec.section or sec.heading or "",
                            "page_number": sec.page_number,
                            "chunk_index": chunk_idx
                        }
                    )
                    chunks.append(chunk_obj)
                    chunk_idx += 1

                    # Create overlap: carry forward the last sentence if it is reasonably short
                    last_s = current_chunk_sentences[-1]
                    if len(last_s) <= self.overlap_chars:
                        current_chunk_sentences = [last_s, sentence]
                        current_len = len(last_s) + sentence_len
                    else:
                        current_chunk_sentences = [sentence]
                        current_len = sentence_len
                else:
                    current_chunk_sentences.append(sentence)
                    current_len += sentence_len

            # Flush final leftover sentences of this section
            if current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences).strip()
                math_found = [m.strip() for m in self.math_regex.findall(chunk_text) if len(m.strip()) > 2]
                chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
                approx_tokens = max(1, len(chunk_text) // 4)

                chunk_obj = EducationalChunk(
                    chunk_id=f"{document_id}_chk_{chunk_idx:03d}",
                    document_id=document_id,
                    source_id=source_id,
                    chunk_index=chunk_idx,
                    chapter=sec.chapter,
                    section=sec.section or sec.heading,
                    page_number=sec.page_number,
                    content=chunk_text,
                    extracted_math=math_found,
                    token_count=approx_tokens,
                    sha256_hash=chunk_hash,
                    metadata={
                        "document_id": document_id,
                        "document_title": extracted.title,
                        "source_id": source_id,
                        "source_name": source_name,
                        "subject": subject,
                        "academic_level": academic_level,
                        "chapter": sec.chapter or "",
                        "section": sec.section or sec.heading or "",
                        "page_number": sec.page_number,
                        "chunk_index": chunk_idx
                    }
                )
                chunks.append(chunk_obj)
                chunk_idx += 1

        return chunks


educational_chunker = EducationalChunkingEngine()

