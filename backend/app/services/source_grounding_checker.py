"""Source-grounding verification service: verifies claims against retrieved chunks and detects insufficient information."""

import re
from typing import List, Tuple, Optional, Set

from app.schemas.rag import RetrievedChunkItem
from app.schemas.validation import FactualClaimCheck


# Common English stopwords to ignore during semantic overlap calculation
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some",
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
    "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're",
    "you've", "your", "yours", "yourself", "yourselves"
}

# Patterns indicating conversational scaffolding rather than testable factual claims
SCAFFOLDING_PATTERNS = [
    r'^(hello|hi|welcome|sure|here is|certainly|let me explain|in summary|conclusion)',
    r'^#+\s+', # Markdown headings
    r'^\*\*pedagogical depth\*\*',
    r'^\*\*step \d+',
    r'^\*\*citation'
]


class SourceGroundingChecker:
    """Verifies that factual assertions in the tutor's response are grounded in retrieved curriculum context."""

    def extract_claims(self, text: str) -> List[str]:
        """Decompose response into atomic, testable factual assertions."""
        # Split on sentence boundaries (. ! ?) and bullet points
        raw_lines = text.split("\n")
        sentences = []

        for line in raw_lines:
            line = line.strip()
            if not line:
                continue

            # Strip bullet markers
            line = re.sub(r'^(\*|-|\d+\.)\s+', '', line)

            # Skip scaffolding or markdown headers
            if any(re.match(pat, line, re.IGNORECASE) for pat in SCAFFOLDING_PATTERNS):
                continue

            # Split into sub-sentences
            parts = re.split(r'(?<=[.!?])\s+', line)
            for p in parts:
                p = p.strip()
                # Keep substantive statements with >= 4 words
                words = p.split()
                if len(words) >= 4 and not p.startswith("#"):
                    sentences.append(p)

        return sentences

    def check_grounding(
        self,
        answer: str,
        retrieved_chunks: List[RetrievedChunkItem],
        min_overlap_threshold: float = 0.28
    ) -> Tuple[List[FactualClaimCheck], bool, Optional[str], float]:
        """
        Verify factual claims against retrieved chunks.
        
        Returns:
            - List of FactualClaimCheck objects
            - insufficient_info_detected (bool)
            - insufficient_info_message (Optional[str])
            - overall_grounding_ratio (float: 0.0 to 1.0)
        """
        # Check for explicit insufficiency indicators
        insufficient_phrases = [
            "insufficient context",
            "not enough information",
            "does not contain enough information",
            "cannot be verified from the retrieved",
            "curriculum materials do not cover",
            "cannot be determined from the curriculum",
            "no verified curriculum materials"
        ]
        explicit_disclaimer = any(phrase in answer.lower() for phrase in insufficient_phrases)

        # 1. Handle case where retrieved chunks were not supplied
        if not retrieved_chunks:
            msg = (
                "The educational knowledge base currently contains no verified curriculum materials matching this inquiry. "
                "The system will not generate unverified claims without authoritative curriculum grounding."
            )
            return (
                [],
                explicit_disclaimer,
                msg if explicit_disclaimer else None,
                0.0
            )

        claims = self.extract_claims(answer)
        if not claims:
            # Short answer or direct formula
            claims = [answer.strip()]

        claim_checks: List[FactualClaimCheck] = []
        grounded_count = 0

        # Pre-tokenize all chunks
        chunk_token_sets = []
        for ch in retrieved_chunks:
            content_lower = ch.content.lower()
            tokens = set(re.findall(r'\b[a-z0-9_]{2,}\b', content_lower)) - STOPWORDS
            # Extract numbers/formulas
            numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', content_lower))
            chunk_token_sets.append({
                "chunk": ch,
                "tokens": tokens,
                "numbers": numbers,
                "raw": content_lower
            })

        # 2. Score each claim
        for claim in claims:
            claim_lower = claim.lower()
            claim_tokens = set(re.findall(r'\b[a-z0-9_]{2,}\b', claim_lower)) - STOPWORDS
            claim_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', claim_lower))

            if not claim_tokens and not claim_numbers:
                continue

            best_score = 0.0
            best_chunk: Optional[RetrievedChunkItem] = None

            for ch_data in chunk_token_sets:
                # Token overlap (Jaccard-like recall against claim)
                token_overlap = len(claim_tokens & ch_data["tokens"]) / max(len(claim_tokens), 1)

                # Number overlap bonus
                num_overlap = 0.0
                if claim_numbers:
                    num_overlap = len(claim_numbers & ch_data["numbers"]) / len(claim_numbers)

                # Substring containment bonus
                clean_claim_snippet = " ".join(list(claim_tokens)[:5])
                substr_bonus = 0.2 if clean_claim_snippet in ch_data["raw"] else 0.0

                score = (0.7 * token_overlap) + (0.2 * num_overlap) + substr_bonus
                score = min(score, 1.0)

                if score > best_score:
                    best_score = score
                    best_chunk = ch_data["chunk"]

            is_grounded = best_score >= min_overlap_threshold
            if is_grounded:
                grounded_count += 1

            claim_checks.append(
                FactualClaimCheck(
                    claim_text=claim,
                    is_grounded=is_grounded,
                    supporting_chunk_id=best_chunk.chunk_id if (best_chunk and is_grounded) else None,
                    supporting_source=best_chunk.source_name if (best_chunk and is_grounded) else None,
                    grounding_score=round(best_score, 3)
                )
            )

        total_checked = len(claim_checks)
        grounding_ratio = (grounded_count / total_checked) if total_checked > 0 else 0.0

        # Check for explicit insufficiency indicators
        insufficient_phrases = [
            "insufficient context",
            "not enough information",
            "does not contain enough information",
            "cannot be verified from the retrieved",
            "curriculum materials do not cover"
        ]
        explicit_disclaimer = any(phrase in answer.lower() for phrase in insufficient_phrases)

        # Insufficient info is triggered if all chunks had low scores (< 0.25) AND grounding ratio is very low
        max_chunk_score = max((ch.rerank_score for ch in retrieved_chunks), default=0.0)
        insufficient_detected = explicit_disclaimer or (max_chunk_score < 0.25 and grounding_ratio < 0.20)

        insufficient_message = None
        if insufficient_detected:
            insufficient_message = (
                "The retrieved curriculum materials do not contain sufficient verified evidence to fully support this topic. "
                "To uphold academic accuracy, the system avoids generating speculative or unverified claims."
            )

        return claim_checks, insufficient_detected, insufficient_message, round(grounding_ratio, 3)


source_grounding_checker = SourceGroundingChecker()
