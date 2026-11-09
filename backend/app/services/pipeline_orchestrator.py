"""Master End-to-End Pipeline Orchestrator for Phase 10.
Integrates Input Detection, Question Extraction, Classification, RAG, Tutoring, Validation, and Neural TTS.
"""

import time
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.schemas.pipeline import (
    PipelineExecutionRequest,
    PipelineExecutionResponse,
    PipelinePerformanceMetrics,
)
from app.services.unified_pipeline import unified_input_pipeline
from app.services.query_processor import query_processor
from app.services.rag_service import rag_service
from app.schemas.rag import RAGQueryRequest
from app.services.tutor_engine import tutor_engine
from app.schemas.tutor import TutorProblemSolveRequest
from app.services.answer_validator import answer_validator
from app.schemas.validation import AnswerValidationRequest
from app.services.speech_normalizer import speech_normalizer
from app.services.voice_service import voice_service
from app.models.session import StudySession, SessionMessage
from app.core.logging import logger


class PipelineOrchestrator:
    """Coordinates the entire educational tutoring pipeline with microsecond latency profiling."""

    async def execute(
        self,
        request: PipelineExecutionRequest,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
        db: Optional[Session] = None
    ) -> PipelineExecutionResponse:
        """Executes the full 10-step unified workflow from multimodal input to synchronized voice response."""
        t_total_start = time.perf_counter()

        # Step 1: Input Detection & Processing
        t_input_start = time.perf_counter()
        if file_bytes:
            input_type = request.input_type or "text"
            extracted_payload = unified_input_pipeline.process(
                input_type=input_type,
                data=file_bytes,
                filename=filename,
                mime_type=mime_type
            )
            extracted_question = extracted_payload.extracted_question
            detected_math = extracted_payload.math_expressions
            resolved_input_type = extracted_payload.input_type
        else:
            raw_text = request.query or "Define the fundamental theorem of algebra."
            extracted_payload = unified_input_pipeline.process(
                input_type="text",
                data=raw_text
            )
            extracted_question = extracted_payload.extracted_question
            detected_math = extracted_payload.math_expressions
            resolved_input_type = "text"
        t_input_end = time.perf_counter()
        input_processing_time_ms = round((t_input_end - t_input_start) * 1000, 2)

        # Step 2: Query Classification
        t_class_start = time.perf_counter()
        normalized_q = query_processor.normalize(extracted_question)
        resolved_subject = request.subject or query_processor.identify_subject(normalized_q)
        query_intent = query_processor.classify_intent(normalized_q)
        t_class_end = time.perf_counter()
        query_classification_time_ms = round((t_class_end - t_class_start) * 1000, 2)

        # Step 3: Curriculum RAG Retrieval
        t_rag_start = time.perf_counter()
        rag_citations: List[Dict[str, Any]] = []
        retrieved_chunks_count = 0
        if db:
            try:
                rag_req = RAGQueryRequest(
                    query=extracted_question,
                    subject=resolved_subject,
                    top_k=3
                )
                rag_out = rag_service.execute_rag(rag_req, db=db)
                retrieved_chunks_count = rag_out.retrieved_chunks_count
                rag_citations = [c.model_dump() for c in rag_out.citations]
            except Exception as e:
                logger.warning(f"RAG retrieval skipped in pipeline: {e}")
        t_rag_end = time.perf_counter()
        retrieval_time_ms = round((t_rag_end - t_rag_start) * 1000, 2)

        # Step 4: Pedagogical Tutoring & SymPy Verification
        t_answer_start = time.perf_counter()
        solve_req = TutorProblemSolveRequest(
            query=extracted_question,
            subject=resolved_subject,
            level=request.level or "intermediate",
            session_id=request.session_id,
            include_rag_curriculum=True
        )
        if db:
            solve_res = tutor_engine.solve_problem(solve_req, db=db)
        else:
            # Fallback when running without DB session
            from app.db.session import SessionLocal
            with SessionLocal() as temp_db:
                solve_res = tutor_engine.solve_problem(solve_req, db=temp_db)

        sympy_verified = solve_res.sympy_verified
        sympy_result = solve_res.sympy_details.get("latex_result") if solve_res.sympy_details else None
        formatted_markdown = solve_res.formatted_markdown
        t_answer_end = time.perf_counter()
        answer_generation_time_ms = round((t_answer_end - t_answer_start) * 1000, 2)

        # Step 5: Answer Validation & Hallucination Control
        t_val_start = time.perf_counter()
        val_req = AnswerValidationRequest(
            question=extracted_question,
            answer=formatted_markdown,
            retrieved_chunks=[],
            citations=solve_res.citations,
            subject=resolved_subject
        )
        val_res = answer_validator.validate_answer(val_req)
        sanitized_markdown = val_res.sanitized_answer
        validation_data = val_res.model_dump()
        t_val_end = time.perf_counter()
        validation_time_ms = round((t_val_end - t_val_start) * 1000, 2)

        # Step 6: Text-to-Speech & Synchronized Subtitles
        t_tts_start = time.perf_counter()
        voice_data = None
        if request.synthesize_voice:
            try:
                from app.schemas.voice import TTSVoiceRequest
                speed = request.playback_speed or 1.0
                rate_str = f"{int((speed - 1.0) * 100):+d}%"
                tts_req = TTSVoiceRequest(
                    text=sanitized_markdown,
                    voice=request.preferred_voice or "en-US-AriaNeural",
                    rate=rate_str
                )
                tts_output = await voice_service.generate_speech_and_subtitles(tts_req)
                voice_data = tts_output.model_dump()
            except Exception as e:
                logger.warning(f"TTS generation skipped in pipeline: {e}")
        t_tts_end = time.perf_counter()
        tts_generation_time_ms = round((t_tts_end - t_tts_start) * 1000, 2)

        # Step 7: Multi-turn Session Persistence
        if request.session_id and db:
            try:
                session = db.query(StudySession).filter(StudySession.id == request.session_id).first()
                if session:
                    # Save user turn
                    user_msg = SessionMessage(
                        session_id=session.id,
                        sender_role="user",
                        content_type=resolved_input_type if resolved_input_type != "text" else "text",
                        content=extracted_question,
                        input_type=resolved_input_type,
                        extracted_question=extracted_question
                    )
                    # Save assistant turn
                    audio_link = voice_data.get("audio_url") if voice_data else None
                    cits_json = json.dumps(rag_citations) if rag_citations else None
                    assistant_msg = SessionMessage(
                        session_id=session.id,
                        sender_role="assistant",
                        content_type="text",
                        content=sanitized_markdown,
                        input_type="text",
                        extracted_question=extracted_question,
                        audio_url=audio_link,
                        citations_json=cits_json,
                        metadata_json=json.dumps({"confidence_score": validation_data.get("confidence_score")})
                    )
                    db.add_all([user_msg, assistant_msg])
                    db.commit()
            except Exception as e:
                logger.warning(f"Session message recording failed in pipeline: {e}")

        # Step 8: Total End-to-End Latency
        t_total_end = time.perf_counter()
        total_response_time_ms = round((t_total_end - t_total_start) * 1000, 2)

        metrics = PipelinePerformanceMetrics(
            input_processing_time_ms=input_processing_time_ms,
            query_classification_time_ms=query_classification_time_ms,
            retrieval_time_ms=retrieval_time_ms,
            answer_generation_time_ms=answer_generation_time_ms,
            validation_time_ms=validation_time_ms,
            tts_generation_time_ms=tts_generation_time_ms,
            total_response_time_ms=total_response_time_ms
        )

        return PipelineExecutionResponse(
            session_id=request.session_id,
            input_type=resolved_input_type,
            extracted_question=extracted_question,
            detected_math=detected_math,
            query_intent=query_intent,
            subject=resolved_subject,
            retrieved_chunks_count=retrieved_chunks_count,
            citations=rag_citations,
            sympy_verified=sympy_verified,
            sympy_result=sympy_result,
            formatted_markdown=sanitized_markdown,
            validation=validation_data,
            voice=voice_data,
            performance_metrics=metrics
        )


pipeline_orchestrator = PipelineOrchestrator()

