"""Educational document study aid generator: chapter summaries, key points, definitions, and revision notes."""

import re
from typing import List, Dict, Any, Optional
from app.schemas.tutor import StudyAidRequest, StudyAidResponse, ExplanationLevel
from app.core.config import settings
from app.core.logging import logger


class EducationalStudyAidGenerator:
    """Generates structured summaries, high-yield revision notes, and definitions from academic text."""

    def __init__(self):
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not load Gemini for study aids: {e}")

    def generate_study_aid(self, request: StudyAidRequest) -> StudyAidResponse:
        """Synthesize educational study materials tailored to the requested aid type and level."""
        content = request.content.strip()
        title = request.title or "Curriculum Study Module"
        level_str = request.level.value if hasattr(request.level, 'value') else str(request.level)

        # 1. Try Gemini cloud generation if available
        if self._gemini_client:
            try:
                prompt = (
                    f"You are an academic curriculum mentor. Analyze the following educational content and generate a "
                    f"comprehensive '{request.aid_type}' tailored for a {level_str} student.\n\n"
                    f"TOPIC TITLE: {title}\n"
                    f"CONTENT:\n{content[:4000]}\n\n"
                    "FORMAT REQUIREMENTS:\n"
                    "- Executive Conceptual Summary (2-3 paragraphs)\n"
                    "- High-Yield Key Points (bulleted)\n"
                    "- Key Glossary Definitions (Term: Definition)\n"
                    "- Quick Revision Tips & LaTeX Formulas ($...$ and $$...$$)\n"
                )
                response = self._gemini_client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=[prompt]
                )
                if response.text and response.text.strip():
                    return self._package_response(title, request.aid_type, level_str, response.text.strip(), content)
            except Exception as e:
                logger.warning(f"Gemini study aid generation failed: {e}. Falling back to local synthesizer.")

        # 2. Deterministic Local Study Aid Synthesizer
        return self._generate_local_study_aid(title, request.aid_type, level_str, content)

    def _generate_local_study_aid(
        self,
        title: str,
        aid_type: str,
        level_str: str,
        content: str
    ) -> StudyAidResponse:
        """Heuristic academic synthesizer extracting key sentences, definitions, and equations."""
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        
        # Extract headings and definitions
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if len(s.strip()) > 20]
        
        summary_paragraphs = []
        if sentences:
            summary_paragraphs.append(" ".join(sentences[:min(3, len(sentences))]))
            if len(sentences) > 4:
                summary_paragraphs.append(" ".join(sentences[3:min(6, len(sentences))]))
        else:
            summary_paragraphs.append(f"Comprehensive curriculum review covering core principles of {title}.")

        summary_text = "\n\n".join(summary_paragraphs)

        # High yield key points
        key_points = []
        for s in sentences:
            if any(kw in s.lower() for kw in ["is defined as", "states that", "proportional to", "therefore", "fundamental", "theorem"]):
                if len(key_points) < 5 and s not in key_points:
                    key_points.append(s)

        if not key_points and sentences:
            key_points = sentences[:min(4, len(sentences))]

        # Key definitions (look for "X is Y" or "X = Y")
        definitions: Dict[str, str] = {}
        for s in sentences:
            match = re.match(r'^([A-Z][\w\s]{2,25})\s+(?:is|refers to|represents)\s+(.+)', s)
            if match and len(definitions) < 4:
                term = match.group(1).strip()
                defn = match.group(2).strip()
                definitions[term] = defn

        # Build clean Markdown document
        md_lines = [
            f"# 📘 Study Guide: {title}",
            f"**Academic Level:** {level_str.capitalize()} | **Resource Type:** {aid_type.replace('_', ' ').capitalize()}\n",
            "## 📝 Executive Summary",
            summary_text,
            "\n## 🔑 Key Points to Remember"
        ]
        for kp in key_points:
            md_lines.append(f"- {kp}")

        if definitions:
            md_lines.append("\n## 📖 Key Definitions")
            for term, defn in definitions.items():
                md_lines.append(f"- **{term}:** {defn}")

        md_lines.append("\n## 💡 Revision Notes & Examination Tips")
        md_lines.append(f"- Review fundamental equations and verify units before substituting values.")
        md_lines.append(f"- Re-derive core formulas step-by-step rather than memorizing isolated numbers.")

        formatted_md = "\n".join(md_lines)

        return StudyAidResponse(
            title=title,
            aid_type=aid_type,
            level=level_str,
            summary_text=summary_text,
            key_points=key_points,
            definitions=definitions,
            formatted_markdown=formatted_md
        )

    def _package_response(
        self,
        title: str,
        aid_type: str,
        level_str: str,
        gemini_text: str,
        content: str
    ) -> StudyAidResponse:
        """Parse Gemini output into structured StudyAidResponse."""
        return StudyAidResponse(
            title=title,
            aid_type=aid_type,
            level=level_str,
            summary_text=gemini_text[:300] + "...",
            key_points=["Detailed pedagogical points synthesized above."],
            definitions={},
            formatted_markdown=gemini_text
        )


study_aid_generator = EducationalStudyAidGenerator()

