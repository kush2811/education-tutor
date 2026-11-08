"""FastAPI endpoints for Phase 8: Text-to-Speech and Synchronized Subtitles."""

import os
import re
from fastapi import APIRouter, status, HTTPException
from fastapi.responses import FileResponse

from app.schemas.voice import (
    TTSVoiceRequest,
    TTSVoiceResponse,
    NormalizeSpeechRequest,
    NormalizeSpeechResponse
)
from app.services.voice_service import voice_service, STORAGE_AUDIO_DIR
from app.services.speech_normalizer import speech_normalizer

router = APIRouter()


@router.post(
    "/generate",
    response_model=TTSVoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate neural TTS audio and timestamped sentence/word subtitle segments"
)
async def generate_speech(request: TTSVoiceRequest):
    """Synthesize natural educational speech and calculate synchronized subtitle timestamps."""
    try:
        return await voice_service.generate_speech_and_subtitles(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech synthesis failed: {str(e)}"
        )


@router.get(
    "/audio/{filename}",
    status_code=status.HTTP_200_OK,
    summary="Stream or download synthesized educational audio file"
)
async def get_audio_file(filename: str):
    """Stream generated MP3 audio file with range and caching headers."""
    # Strict filename validation preventing directory traversal
    if not re.match(r'^[a-fA-F0-9]{32}\.(?:mp3|wav)$', filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid audio filename format."
        )

    file_path = os.path.join(STORAGE_AUDIO_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested audio file not found."
        )

    media_type = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@router.post(
    "/normalize",
    response_model=NormalizeSpeechResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspect speech normalization on academic markdown, math formulas, and code blocks"
)
async def normalize_speech(request: NormalizeSpeechRequest):
    """Convert structured academic markdown into fluid spoken sentences without synthesizing audio."""
    pairs = speech_normalizer.split_into_sentence_pairs(request.text)
    spoken_script = " ".join(spoken for _, spoken in pairs)
    sentence_pairs = [{"display_text": d, "spoken_text": s} for d, s in pairs]

    return NormalizeSpeechResponse(
        original_text=request.text,
        spoken_script=spoken_script,
        sentence_pairs=sentence_pairs
    )

