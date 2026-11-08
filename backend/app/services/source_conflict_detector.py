"""Source conflict detection service: identifies contradictions between retrieved excerpts and applies source authority policy."""

import re
from typing import List, Tuple, Dict, Any, Optional

from app.schemas.rag import RetrievedChunkItem
from app.schemas.validation import SourceConflict

# Authoritative hierarchy mapping per Phase 4 source quality policy
AUTHORITY_TIER_SCORES: Dict[str, int] = {
    "National Curriculum": 100,
    "National Curriculum Body": 100,
    "NCERT": 100,
    "Government Educational Portal": 90,
    "Government Portal": 90,
    "Official University Material": 80,
    "Official University": 80,
    "OpenStax": 80,
    "MIT OpenCourseWare": 80,
    "Official Language Documentation": 75,
    "Official Documentation": 75,
    "Open Educational Resource": 70,
    "OER": 70,
    "Academic Research Source": 65,
    "arXiv": 65,
    "General": 50
}

# Known academic duality patterns in STEM where different curricula use differing conventions
KNOWN_STEM_DUALITIES = [
    {
        "pattern": r'\b(thermodynamics|first law|work done|internal energy|\bq\s*[-+]\s*w\b)',
        "topic": "First Law of Thermodynamics (Sign Convention for Work)",
        "convention_a": r'(\bq\s*-\s*w\b|work done by the system)',
        "claim_a": "First Law expressed as ΔU = Q - W (Physics convention: W is work done by the system)",
        "convention_b": r'(\bq\s*\+\s*w\b|work done on the system)',
        "claim_b": "First Law expressed as ΔU = Q + W (IUPAC / Chemistry convention: W is work done on the system)"
    },
    {
        "pattern": r'\b(natural numbers?|\bwhole numbers?|\b0 is\b|\bzero is\b)',
        "topic": "Inclusion of Zero in Natural Numbers (N)",
        "convention_a": r'(includes? zero|including 0|starts? at 0|\{0,\s*1)',
        "claim_a": "Natural numbers defined as {0, 1, 2, ...} (ISO 80000-2 & Computer Science convention)",
        "convention_b": r'(positive integers?|starts? at 1|excludes? zero|\{1,\s*2)',
        "claim_b": "Natural numbers defined as {1, 2, 3, ...} excluding zero (Classical Arithmetic convention)"
    },
    {
        "pattern": r'\b(acceleration due to gravity|\bg\s*=\s*\d+)',
        "topic": "Standard Value for Acceleration Due to Gravity (g)",
        "convention_a": r'\b9\.81\b',
        "claim_a": "g approximated as 9.81 m/s² (University / International standard)",
        "convention_b": r'\b(9\.8(?!\d)|10\b)',
        "claim_b": "g approximated as 9.8 m/s² or rounded to 10 m/s² for high-school examination calculation"
    }
]


class SourceConflictDetector:
    """Detects factual or definitional contradictions among retrieved curriculum chunks and resolves them via authority tiering."""

    def get_authority_weight(self, authority_str: Optional[str]) -> int:
        """Map authority string to numeric hierarchy weight."""
        if not authority_str:
            return 50
        for key, weight in AUTHORITY_TIER_SCORES.items():
            if key.lower() in authority_str.lower():
                return weight
        return 50

    def detect_conflicts(self, chunks: List[RetrievedChunkItem]) -> List[SourceConflict]:
        """Inspect all pairs of retrieved chunks to identify and resolve factual or conventional discrepancies."""
        conflicts: List[SourceConflict] = []
        if len(chunks) < 2:
            return conflicts

        detected_topics = set()

        # Check known STEM conventional dualities
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                chunk_a = chunks[i]
                chunk_b = chunks[j]

                text_a = chunk_a.content.lower()
                text_b = chunk_b.content.lower()

                for duality in KNOWN_STEM_DUALITIES:
                    if duality["topic"] in detected_topics:
                        continue

                    # Check if both chunks touch on the duality topic
                    touches_a = bool(re.search(duality["pattern"], text_a))
                    touches_b = bool(re.search(duality["pattern"], text_b))

                    if touches_a and touches_b:
                        has_conv_a_in_1 = bool(re.search(duality["convention_a"], text_a))
                        has_conv_b_in_2 = bool(re.search(duality["convention_b"], text_b))

                        has_conv_b_in_1 = bool(re.search(duality["convention_b"], text_a))
                        has_conv_a_in_2 = bool(re.search(duality["convention_a"], text_b))

                        # If they represent opposing sides of the convention
                        if (has_conv_a_in_1 and has_conv_b_in_2) or (has_conv_b_in_1 and has_conv_a_in_2):
                            auth_a = self.get_authority_weight(chunk_a.authority)
                            auth_b = self.get_authority_weight(chunk_b.authority)

                            resolved = False
                            pref_source = None
                            rationale = ""

                            if auth_a > auth_b:
                                resolved = True
                                pref_source = chunk_a.source_name
                                rationale = (
                                    f"Resolved in favor of '{chunk_a.source_name}' ({chunk_a.authority}, tier weight {auth_a}) "
                                    f"over '{chunk_b.source_name}' ({chunk_b.authority}, tier weight {auth_b}) per curriculum hierarchy policy."
                                )
                            elif auth_b > auth_a:
                                resolved = True
                                pref_source = chunk_b.source_name
                                rationale = (
                                    f"Resolved in favor of '{chunk_b.source_name}' ({chunk_b.authority}, tier weight {auth_b}) "
                                    f"over '{chunk_a.source_name}' ({chunk_a.authority}, tier weight {auth_a}) per curriculum hierarchy policy."
                                )
                            else:
                                resolved = False
                                pref_source = None
                                rationale = (
                                    f"Unresolved academic convention divergence: Both '{chunk_a.source_name}' and '{chunk_b.source_name}' "
                                    f"possess equal authority weight ({auth_a}). The system presents both conventions explicitly to the student."
                                )

                            conflicts.append(
                                SourceConflict(
                                    topic_or_entity=duality["topic"],
                                    source_a_name=chunk_a.source_name,
                                    source_a_authority=chunk_a.authority,
                                    source_a_claim=duality["claim_a"] if has_conv_a_in_1 else duality["claim_b"],
                                    source_b_name=chunk_b.source_name,
                                    source_b_authority=chunk_b.authority,
                                    source_b_claim=duality["claim_b"] if has_conv_a_in_1 else duality["claim_a"],
                                    resolved=resolved,
                                    preferred_source=pref_source,
                                    resolution_rationale=rationale
                                )
                            )
                            detected_topics.add(duality["topic"])

        return conflicts


source_conflict_detector = SourceConflictDetector()

