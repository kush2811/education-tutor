"""Context construction and citation mapping for educational RAG prompts."""

from typing import List, Tuple
from app.schemas.rag import RetrievedChunkItem, RAGCitation


class EducationalContextBuilder:
    """Assembles retrieved curriculum excerpts and builds verified citation cards."""

    def build_context(self, chunks: List[RetrievedChunkItem]) -> Tuple[str, List[RAGCitation], bool]:
        """Convert retrieved curriculum chunks into an annotated context block for the LLM.
        
        Returns:
            Tuple of (formatted_context_str, list_of_rag_citations, is_context_sufficient)
        """
        if not chunks:
            return (
                "NO VERIFIED CURRICULUM CONTEXT FOUND IN KNOWLEDGE BASE.",
                [],
                False
            )

        context_cards: List[str] = []
        citations: List[RAGCitation] = []

        for idx, chk in enumerate(chunks, 1):
            label = f"[{idx}]"
            chapter_info = chk.chapter or "General Curriculum"
            section_info = chk.section or ""
            page_info = f"Page {chk.page_number}"
            
            # Bibliographic citation string
            bib_parts = [chk.source_name]
            if chk.chapter:
                bib_parts.append(chk.chapter)
            if chk.section:
                bib_parts.append(chk.section)
            bib_parts.append(page_info)
            bib_parts.append(f"({chk.authority})")
            bib_str = ", ".join(bib_parts)

            card_text = (
                f"{label} SOURCE: {chk.source_name} | {chapter_info} | {section_info} | {page_info}\n"
                f"AUTHORITY: {chk.authority} | LICENSE: {chk.license_type}\n"
                f"CANONICAL URL: {chk.source_url}\n"
                f"CURRICULUM EXCERPT:\n{chk.content}\n"
            )
            context_cards.append(card_text)

            citations.append(RAGCitation(
                source_id=chk.source_id,
                source_name=chk.source_name,
                source_url=chk.source_url,
                chapter=chk.chapter,
                section=chk.section,
                page_number=chk.page_number,
                authority=chk.authority,
                license_type=chk.license_type,
                citation_label=label,
                citation_text=bib_str,
                excerpt=chk.content[:250] + ("..." if len(chk.content) > 250 else "")
            ))

        formatted_context = "\n---\n".join(context_cards)
        # Context is sufficient if at least one candidate meets quality threshold
        is_sufficient = len(chunks) > 0 and chunks[0].rerank_score >= 0.25

        return formatted_context, citations, is_sufficient


context_builder = EducationalContextBuilder()
