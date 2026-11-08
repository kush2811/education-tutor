"""Text normalization service for student inquiries and mathematical questions."""

import re
from typing import List, Tuple
from app.schemas.unified_input import UnifiedQuestionPayload
from app.core.logging import logger


class TextNormalizer:
    """Accepts student questions, cleans formatting, normalizes math notation, and extracts formulas."""

    # Subject keyword heuristics
    SUBJECT_PATTERNS = {
        "Mathematics": [r"\bderivative\b", r"\bintegral\b", r"\bequation\b", r"\bfactor\b", r"\bmatrix\b", r"\bpolynomial\b", r"\blimit\b", r"\bquadratic\b", r"\btriangle\b", r"\bangle\b"],
        "Physics": [r"\bvelocity\b", r"\bacceleration\b", r"\bforce\b", r"\bmomentum\b", r"\benergy\b", r"\bcircuit\b", r"\bcurrent\b", r"\bvoltage\b", r"\bgravity\b", r"\bthermodynamics\b"],
        "Chemistry": [r"\breaction\b", r"\bmol\b", r"\bacid\b", r"\bbase\b", r"\belement\b", r"\belectron\b", r"\bequilibrium\b", r"\bstoichiometry\b", r"\bcompound\b"],
        "Computer Science": [r"\balgorithm\b", r"\bcomplexity\b", r"\bcode\b", r"\bfunction\b", r"\barray\b", r"\btree\b", r"\bgraph\b", r"\brecursion\b", r"\bpython\b", r"\bjava\b"],
    }

    def normalize_text(self, text: str) -> str:
        """Sanitize whitespace, fix line breaks, and convert bracket math to standard LaTeX delimiters."""
        if not text:
            return ""

        # Normalize line endings
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

        # Convert \[ ... \] to $$ ... $$ and \( ... \) to $ ... $
        cleaned = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\\\((.*?)\\\)", r"$\1$", cleaned, flags=re.DOTALL)

        # Normalize Unicode math symbols to standard ASCII / LaTeX equivalents
        cleaned = cleaned.replace("×", "*").replace("÷", "/").replace("−", "-")
        cleaned = re.sub(r"√(\w+)", r"\\sqrt{\1}", cleaned)

        # Collapse excess whitespace while preserving paragraph breaks
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    def extract_math_formulas(self, text: str) -> List[str]:
        """Extract all LaTeX formulas encapsulated in $...$ or $$...$$."""
        formulas = []
        # Find block math
        block_matches = re.findall(r"\$\$(.*?)\$\$", text, flags=re.DOTALL)
        formulas.extend([m.strip() for m in block_matches if m.strip()])

        # Find inline math (excluding block $$)
        # Temporarily replace block with token to avoid double capture
        temp_text = re.sub(r"\$\$.*?\$\$", "___BLOCK_MATH___", text, flags=re.DOTALL)
        inline_matches = re.findall(r"\$([^\$]+?)\$", temp_text)
        formulas.extend([m.strip() for m in inline_matches if m.strip()])

        return formulas

    def detect_subject(self, text: str) -> str:
        """Infer subject domain using regex keyword matching."""
        lower = text.lower()
        for subject, patterns in self.SUBJECT_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower):
                    return subject
        return "General STEM"

    def process_text_question(self, raw_text: str) -> UnifiedQuestionPayload:
        """Normalize raw student text and produce a UnifiedQuestionPayload."""
        normalized = self.normalize_text(raw_text)
        math_formulas = self.extract_math_formulas(normalized)
        subject = self.detect_subject(normalized)

        logger.info(f"Normalized student text ({len(normalized)} chars, {len(math_formulas)} formulas, subject={subject})")

        return UnifiedQuestionPayload(
            input_type="text",
            extracted_question=normalized,
            extracted_context=f"Subject detected: {subject}",
            math_expressions=math_formulas,
            confidence_score=1.0,
            metadata={"detected_subject": subject, "char_count": len(normalized)}
        )


text_normalizer = TextNormalizer()

