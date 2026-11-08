"""Query processing, normalization, classification, subject identification, and expansion for educational RAG."""

import re
from typing import Dict, Any, Tuple, List, Optional
from app.services.knowledge_cleaner import content_cleaner


class EducationalQueryProcessor:
    """Preprocesses, classifies, and enriches student academic queries for curriculum retrieval."""

    SUBJECT_KEYWORDS: Dict[str, List[str]] = {
        "Mathematics": [
            "derivative", "integral", "limit", "matrix", "determinant", "quadratic", "polynomial",
            "trigonometry", "sine", "cosine", "tangent", "triangle", "geometry", "algebra",
            "calculus", "vector", "probability", "statistics", "equation", "theorem", "logarithm"
        ],
        "Physics": [
            "velocity", "acceleration", "force", "gravity", "friction", "momentum", "energy",
            "work", "kinetic", "potential", "thermodynamics", "entropy", "wavelength", "frequency",
            "optics", "electromagnetism", "current", "voltage", "resistance", "newton", "inertia"
        ],
        "Chemistry": [
            "molecule", "atom", "electron", "proton", "neutron", "orbital", "covalent", "ionic",
            "reaction", "acid", "base", "ph", "equilibrium", "thermodynamics", "organic", "polymer",
            "periodic table", "oxidation", "reduction", "solution", "molarity"
        ],
        "Biology": [
            "cell", "mitochondria", "dna", "rna", "protein", "enzyme", "genetics", "photosynthesis",
            "respiration", "organism", "evolution", "ecosystem", "membrane", "chromosome"
        ],
        "Computer Science": [
            "algorithm", "array", "binary search", "sorting", "complexity", "graph", "tree",
            "function", "recursion", "class", "object", "python", "javascript", "data structure",
            "dynamic programming", "hash map", "time complexity"
        ]
    }

    STEM_EXPANSIONS: Dict[str, List[str]] = {
        "derivative": ["rate of change", "instantaneous slope", "tangent line", "differentiation"],
        "integral": ["area under curve", "antiderivative", "definite integral", "riemann sum"],
        "quadratic": ["roots", "discriminant", "ax^2 + bx + c = 0", "quadratic formula"],
        "newton": ["laws of motion", "inertia", "F = ma", "action and reaction"],
        "momentum": ["mass times velocity", "p = mv", "conservation of momentum", "impulse"],
        "covalent": ["electron sharing", "chemical bonding", "valence electrons", "molecular structure"],
        "ionic": ["electron transfer", "electrostatic attraction", "cation", "anion"],
        "pythagoras": ["right-angled triangle", "hypotenuse", "a^2 + b^2 = c^2"],
        "binary search": ["divide and conquer", "sorted array", "logarithmic time", "O(log n)"]
    }

    def normalize(self, query: str) -> str:
        """Clean whitespace and standardize bracket LaTeX expressions."""
        if not query:
            return ""
        cleaned = content_cleaner.clean_text(query)
        # Condense spacing
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def identify_subject(self, query: str) -> str:
        """Classify query into appropriate STEM subject domain."""
        query_lower = query.lower()
        subject_scores: Dict[str, int] = {k: 0 for k in self.SUBJECT_KEYWORDS}

        for subject, keywords in self.SUBJECT_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    subject_scores[subject] += 1

        best_subject = max(subject_scores, key=subject_scores.get)
        if subject_scores[best_subject] > 0:
            return best_subject
        return "General STEM"

    def classify_intent(self, query: str) -> str:
        """Detect student query intent for targeted tutoring."""
        q = query.lower()
        if any(w in q for w in ["formula for", "equation of", "state the law", "state the theorem"]):
            return "formula_lookup"
        elif any(w in q for w in ["how to solve", "step by step", "calculate", "find the value", "prove that"]):
            return "step_by_step_solution"
        elif any(w in q for w in ["why does", "how does", "explain why", "conceptual"]):
            return "conceptual_explanation"
        elif any(w in q for w in ["what is", "define", "definition of", "explain the term", "meaning of"]):
            return "definition"
        return "general_inquiry"

    def expand_query(self, query: str, subject: Optional[str] = None) -> str:
        """Expand student query with domain-specific pedagogical synonyms and theorems."""
        query_lower = query.lower()
        expansion_terms: List[str] = []

        for key, synonyms in self.STEM_EXPANSIONS.items():
            if key in query_lower:
                for syn in synonyms:
                    if syn not in query_lower and syn not in expansion_terms:
                        expansion_terms.append(syn)

        if not expansion_terms:
            return query

        expanded = f"{query} ({', '.join(expansion_terms[:3])})"
        return expanded

    def extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract academic level or subject hints from the prompt text."""
        filters: Dict[str, Any] = {}
        q = query.lower()

        # Grade level extraction
        grade_match = re.search(r'(?:grade|class)\s*(1[0-2]|[6-9])', q)
        if grade_match:
            grade_num = grade_match.group(1)
            if grade_num == "10":
                filters["academic_level"] = "Secondary (Grade 10)"
            elif grade_num == "11":
                filters["academic_level"] = "Higher Secondary (Grade 11)"
            elif grade_num == "12":
                filters["academic_level"] = "Higher Secondary (Grade 12)"

        if any(w in q for w in ["college", "university", "undergraduate"]):
            filters["academic_level"] = "Undergraduate"

        return filters


query_processor = EducationalQueryProcessor()
