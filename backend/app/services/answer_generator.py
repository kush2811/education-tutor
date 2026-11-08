"""Educational answer generation engine with curriculum grounding, anti-hallucination guardrails, and citation integration."""

from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.schemas.rag import RAGCitation


class EducationalAnswerGenerator:
    """Generates pedagogically sound, grounded educational explanations using retrieved curriculum cards."""

    INSUFFICIENT_CONTEXT_MESSAGE = (
        "Based on the verified curriculum materials indexed in our knowledge base, there is insufficient "
        "curriculum context to answer this question reliably. To ensure academic rigor and prevent misconceptions, "
        "I do not provide unverified or fabricated answers. Please consult your official textbook or upload the relevant chapter."
    )

    def __init__(self):
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("AnswerGenerator initialized with Google Gemini 1.5 Flash.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}. Using deterministic local generator.")

    def generate_answer(
        self,
        query: str,
        context_str: str,
        citations: List[RAGCitation],
        is_sufficient: bool,
        subject: str
    ) -> Tuple[str, List[RAGCitation]]:
        """Synthesize an educational explanation strictly grounded on the retrieved reference cards.
        
        Returns:
            Tuple of (answer_text, verified_citations_list)
        """
        # If retrieval yielded no sufficient curriculum context, communicate uncertainty immediately
        if not is_sufficient or not citations:
            return self.INSUFFICIENT_CONTEXT_MESSAGE, []

        # 1. Try Gemini 1.5 Flash if available
        if self._gemini_client:
            try:
                system_prompt = (
                    "You are an authoritative, patient AI Multimodal STEM Tutor. Your explanations must be "
                    "strictly grounded in the verified educational reference cards provided below.\n\n"
                    "PEDAGOGICAL INSTRUCTIONS:\n"
                    "1. Answer using ONLY information, theorems, and definitions present in the reference cards.\n"
                    "2. Explain concepts step-by-step with clear, accessible academic prose.\n"
                    "3. Cite supporting facts with bracketed reference numbers like [1], [2] corresponding to the reference cards.\n"
                    "4. Do NOT make unsupported claims or introduce unverified facts.\n"
                    "5. Format all mathematical equations in LaTeX KaTeX: inline with $...$ and display with $$...$$.\n"
                    "6. If the context does not fully cover the student question, explicitly acknowledge the missing information.\n"
                    "7. Never fabricate book titles, URLs, or page numbers."
                )

                user_content = (
                    f"STUDENT QUESTION:\n{query}\n\n"
                    f"VERIFIED CURRICULUM CONTEXT:\n{context_str}\n\n"
                    "Please provide a complete, clear, and citation-backed Socratic answer:"
                )

                response = self._gemini_client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=[system_prompt, user_content]
                )
                if response.text and response.text.strip():
                    return response.text.strip(), citations
            except Exception as e:
                logger.warning(f"Gemini answer generation failed: {e}. Using deterministic local generator fallback.")

        # 2. Deterministic Local Educational Generator Fallback
        return self._generate_local_grounded_answer(query, citations, subject)

    def _generate_local_grounded_answer(
        self,
        query: str,
        citations: List[RAGCitation],
        subject: str
    ) -> Tuple[str, List[RAGCitation]]:
        """Synthesizes a structured educational answer from retrieved cards without external API calls."""
        primary_ref = citations[0]
        ref_label = primary_ref.citation_label
        
        # Build answer sections
        paragraphs = []
        paragraphs.append(f"### Conceptual Overview: {query.strip().capitalize()}\n")
        
        # Grounding paragraph based on primary citation excerpt
        cleaned_excerpt = primary_ref.excerpt.strip().replace("\n", " ")
        if len(cleaned_excerpt) > 200:
            cleaned_excerpt = cleaned_excerpt[:200] + "..."

        paragraphs.append(
            f"According to the verified curriculum from **{primary_ref.source_name}** {ref_label}, "
            f"the core concept can be understood as follows: {cleaned_excerpt}\n"
        )

        # Mathematical or structured breakdown
        if len(citations) > 1:
            sec_ref = citations[1]
            paragraphs.append(
                f"Furthermore, in **{sec_ref.source_name}** ({sec_ref.chapter or 'Key Section'}) {sec_ref.citation_label}, "
                f"it is detailed that: {sec_ref.excerpt.strip()[:180]}...\n"
            )

        paragraphs.append("### Key Takeaways")
        paragraphs.append(f"- **Official Curriculum Anchor:** Verified via {primary_ref.source_name} ({primary_ref.chapter or 'Curriculum Chapter'}, {primary_ref.citation_text}).")
        paragraphs.append(f"- **Authority & Licensing:** Published by {primary_ref.authority} under {primary_ref.license_type}.")

        return "\n".join(paragraphs), citations


answer_generator = EducationalAnswerGenerator()
