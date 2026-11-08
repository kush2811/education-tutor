"""Unified multimodal input pipeline router."""

from typing import Optional, Union, Dict, Any
from app.core.logging import logger
from app.schemas.unified_input import UnifiedQuestionPayload
from app.services.text_normalizer import text_normalizer
from app.services.image_processor import image_processor
from app.services.pdf_processor import pdf_processor
from app.services.docx_processor import docx_processor
from app.services.audio_processor import audio_processor
from app.services.video_processor import video_processor


class UnifiedInputPipeline:
    """Master orchestrator converting ANY multimodal input (text, image, pdf, docx, audio, video)
    into a standardized UnifiedQuestionPayload for the Socratic tutoring engine."""

    def process(
        self,
        input_type: str,
        data: Union[str, bytes],
        filename: Optional[str] = None,
        mime_type: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> UnifiedQuestionPayload:
        """Route input to its designated specialized processor and return a normalized UnifiedQuestionPayload."""
        normalized_type = input_type.lower().strip()
        logger.info(f"UnifiedInputPipeline: routing input_type='{normalized_type}', filename='{filename}'")

        try:
            if normalized_type == "text":
                text_content = data if isinstance(data, str) else data.decode("utf-8", errors="replace")
                return text_normalizer.process_text_question(text_content)

            elif normalized_type == "image":
                raw_bytes = data if isinstance(data, bytes) else data.encode("utf-8")
                return image_processor.process_image(
                    image_bytes=raw_bytes,
                    filename=filename or "problem_image.jpg",
                    file_path=file_path
                )

            elif normalized_type == "pdf":
                raw_bytes = data if isinstance(data, bytes) else data.encode("utf-8")
                return pdf_processor.process_pdf(
                    pdf_bytes=raw_bytes,
                    filename=filename or "worksheet.pdf",
                    file_path=file_path
                )

            elif normalized_type == "docx":
                raw_bytes = data if isinstance(data, bytes) else data.encode("utf-8")
                return docx_processor.process_docx(
                    docx_bytes=raw_bytes,
                    filename=filename or "document.docx",
                    file_path=file_path
                )

            elif normalized_type == "audio":
                raw_bytes = data if isinstance(data, bytes) else data.encode("utf-8")
                return audio_processor.process_audio(
                    audio_bytes=raw_bytes,
                    filename=filename or "question_audio.wav",
                    mime_type=mime_type or "audio/wav",
                    file_path=file_path
                )

            elif normalized_type == "video":
                raw_bytes = data if isinstance(data, bytes) else data.encode("utf-8")
                return video_processor.process_video(
                    video_bytes=raw_bytes,
                    filename=filename or "lecture_clip.mp4",
                    mime_type=mime_type or "video/mp4",
                    file_path=file_path
                )

            else:
                raise ValueError(f"Unsupported input type '{input_type}'. Must be text, image, pdf, docx, audio, or video.")

        except Exception as exc:
            logger.error(f"UnifiedInputPipeline failed for input_type '{input_type}': {exc}", exc_info=True)
            return UnifiedQuestionPayload(
                input_type=normalized_type,
                extracted_question=f"Failed to process {normalized_type} input.",
                processing_status="error",
                error_detail=str(exc),
                confidence_score=0.0
            )


unified_input_pipeline = UnifiedInputPipeline()

