"""Master answer validation coordinator: orchestrates citation checks, source-grounding, conflict resolution, and consistency auditing."""

from typing import List, Optional

from app.schemas.validation import (
    AnswerValidationRequest,
    AnswerValidationResult,
    GroundingStatus,
    CitationCheckStatus,
)
from app.services.citation_validator import citation_validator
from app.services.source_grounding_checker import source_grounding_checker
from app.services.source_conflict_detector import source_conflict_detector
from app.services.answer_consistency_checker import answer_consistency_checker


class AnswerValidator:
    """Intermediary validation and hallucination control layer positioned between AI answer generation and student output."""

    def validate_answer(self, request: AnswerValidationRequest) -> AnswerValidationResult:
        """Execute end-to-end validation pipeline across citations, grounding, conflicts, and consistency."""
        warnings: List[str] = []

        # 1. Citation Validation
        citation_audits, sanitized_answer, cit_warnings = citation_validator.validate_citations(
            answer=request.answer,
            citations=request.citations,
            retrieved_chunks=request.retrieved_chunks
        )
        warnings.extend(cit_warnings)

        # 2. Source Grounding & Insufficient Information Detection
        factual_claims, insufficient_detected, insufficient_msg, grounding_ratio = (
            source_grounding_checker.check_grounding(
                answer=request.answer,
                retrieved_chunks=request.retrieved_chunks
            )
        )
        if insufficient_detected:
            warnings.append("Insufficient curriculum coverage detected: Answer relies on ungrounded or incomplete sources.")

        # 3. Source Conflict Detection
        source_conflicts = source_conflict_detector.detect_conflicts(request.retrieved_chunks)
        for conflict in source_conflicts:
            if not conflict.resolved:
                warnings.append(f"Unresolved academic conflict between sources regarding '{conflict.topic_or_entity}'.")
            else:
                warnings.append(f"Source convention conflict resolved: {conflict.resolution_rationale}")

        # 4. Consistency Auditing (Relevance, Logic, Math via SymPy, Code via AST)
        consistency = answer_consistency_checker.check_consistency(
            question=request.question,
            answer=request.answer,
            code_snippets=request.code_snippets
        )
        if not consistency.addresses_question:
            warnings.append("Relevance warning: Response may not directly address the student's question.")
        if not consistency.calculations_consistent:
            warnings.extend(consistency.math_discrepancies)
        if not consistency.code_safe_and_plausible:
            warnings.extend(consistency.code_issues)

        # 5. Determine Transparent Grounding Status (No arbitrary pseudo-scientific percentages)
        has_phantom_citations = any(c.status == CitationCheckStatus.PHANTOM_INDEX for c in citation_audits)
        has_math_errors = not consistency.calculations_consistent
        has_code_violations = not consistency.code_safe_and_plausible
        has_relevance_fail = not consistency.addresses_question

        if has_math_errors or has_code_violations or has_relevance_fail:
            grounding_status = GroundingStatus.INSUFFICIENTLY_VERIFIED
            explanation = (
                "Status: Insufficiently Verified. "
                "Automated verification flagged discrepancies (e.g. mathematical inconsistencies, "
                "code execution constraints, or off-topic deviation). "
                "The student is advised to verify this result with an educator."
            )
            overall_valid = False
        elif insufficient_detected:
            grounding_status = GroundingStatus.INSUFFICIENTLY_VERIFIED
            explanation = (
                "Status: Insufficiently Verified. "
                "The educational knowledge base does not contain sufficient verified materials for this inquiry. "
                "The system explicitly communicates this limitation to prevent hallucinated answers."
            )
            overall_valid = False
        elif has_phantom_citations:
            grounding_status = GroundingStatus.INSUFFICIENTLY_VERIFIED
            explanation = (
                "Status: Insufficiently Verified. "
                "One or more citation markers in the answer do not exist in the retrieved curriculum sources."
            )
            overall_valid = False
        elif request.retrieved_chunks and grounding_ratio >= 0.40:
            grounding_status = GroundingStatus.SUPPORTED_BY_SOURCES
            supported_count = sum(1 for c in factual_claims if c.is_grounded)
            explanation = (
                f"Status: Supported by Retrieved Sources. "
                f"{supported_count} of {len(factual_claims)} key factual statements are directly anchored in verified curriculum "
                f"documents from authoritative bodies. Citations match indexed sources."
            )
            overall_valid = True
        else:
            grounding_status = GroundingStatus.GENERAL_MODEL_KNOWLEDGE
            explanation = (
                "Status: General Model Knowledge. "
                "The pedagogical explanation and logical steps are internally consistent, "
                "but specific claims could not be tied to indexed curriculum documents."
            )
            overall_valid = True

        # Append transparent audit notice to sanitized output if issues were flagged
        if warnings or source_conflicts or not overall_valid:
            notice_lines = ["\n\n---", "### 🛡️ Answer Verification & Audit Notice"]
            notice_lines.append(f"**Verification Tier:** `{grounding_status.value.replace('_', ' ').title()}`")
            notice_lines.append(f"- **Summary:** {explanation}")

            if source_conflicts:
                notice_lines.append("- **Academic Source Perspective:**")
                for sc in source_conflicts:
                    notice_lines.append(f"  - *{sc.topic_or_entity}:* {sc.resolution_rationale}")

            if warnings:
                notice_lines.append("- **Verification Notes & Disclaimers:**")
                for w in warnings[:4]:
                    notice_lines.append(f"  - {w}")

            sanitized_answer += "\n" + "\n".join(notice_lines)

        return AnswerValidationResult(
            is_valid=overall_valid,
            grounding_status=grounding_status,
            grounding_explanation=explanation,
            factual_claims=factual_claims,
            citation_audit=citation_audits,
            source_conflicts=source_conflicts,
            consistency=consistency,
            insufficient_info_detected=insufficient_detected,
            insufficient_info_message=insufficient_msg,
            sanitized_answer=sanitized_answer,
            warnings=warnings
        )


answer_validator = AnswerValidator()
