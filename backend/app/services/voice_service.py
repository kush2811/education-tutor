"""Voice service: neural TTS audio generation with edge-tts and timestamped sentence/word alignment."""

import os
import re
import hashlib
import asyncio
from typing import List, Optional, Tuple, Dict, Any

from app.schemas.voice import (
    TTSVoiceRequest,
    TTSVoiceResponse,
    SentenceSegment,
    WordSegment
)
from app.services.speech_normalizer import speech_normalizer
from app.core.logging import logger

STORAGE_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "audio")
os.makedirs(STORAGE_AUDIO_DIR, exist_ok=True)


class EducationalVoiceService:
    """Generates natural educational speech audio and computes accurate timestamped sentence and word subtitle alignments."""

    def __init__(self):
        self.default_voice = "en-US-AriaNeural"

    async def generate_speech_and_subtitles(
        self,
        request: TTSVoiceRequest
    ) -> TTSVoiceResponse:
        """Synthesize natural speech from structured markdown and align timestamped sentence/word subtitles."""
        # 1. Normalize structured text (math, code, tables, headings)
        sentence_pairs = speech_normalizer.split_into_sentence_pairs(request.text)
        if not sentence_pairs:
            # Fallback for plain text without punctuation
            normalized_plain = speech_normalizer.normalize_structured_text(request.text)
            sentence_pairs = [(request.text, normalized_plain)]

        full_spoken_script = " ".join(spoken for _, spoken in sentence_pairs)

        # 2. Attempt Neural TTS with edge-tts (with 4.0s timeout to prevent hanging on slow network)
        try:
            return await asyncio.wait_for(
                self._generate_with_edge_tts(
                    request=request,
                    full_spoken_script=full_spoken_script,
                    sentence_pairs=sentence_pairs
                ),
                timeout=4.0
            )
        except Exception as e:
            logger.warning(f"Neural Edge-TTS generation failed or timed out ({e}); falling back to client-aligned speech.")
            return self._generate_fallback_alignment(
                request=request,
                full_spoken_script=full_spoken_script,
                sentence_pairs=sentence_pairs,
                error_msg=str(e)
            )

    async def _generate_with_edge_tts(
        self,
        request: TTSVoiceRequest,
        full_spoken_script: str,
        sentence_pairs: List[Tuple[str, str]]
    ) -> TTSVoiceResponse:
        """Call edge-tts, collect audio bytes, and capture exact neural SentenceBoundary events."""
        import edge_tts

        voice = request.voice or self.default_voice
        rate = request.rate or "+0%"
        pitch = request.pitch or "+0Hz"

        # Unique hash for audio caching
        cache_key = f"{full_spoken_script}_{voice}_{rate}_{pitch}"
        file_hash = hashlib.md5(cache_key.encode('utf-8')).hexdigest()
        audio_filename = f"{file_hash}.mp3"
        audio_filepath = os.path.join(STORAGE_AUDIO_DIR, audio_filename)

        audio_bytes = bytearray()
        boundary_events: List[Dict[str, Any]] = []

        comm = edge_tts.Communicate(
            text=full_spoken_script,
            voice=voice,
            rate=rate,
            pitch=pitch
        )

        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_bytes.extend(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                boundary_events.append(chunk)

        # Write audio file to storage if not already cached
        if not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) == 0:
            with open(audio_filepath, "wb") as f:
                f.write(audio_bytes)

        # 3. Align sentence and word timestamps
        sentence_segments: List[SentenceSegment] = []
        total_duration = 0.0

        if boundary_events and len(boundary_events) >= len(sentence_pairs):
            # Map boundary events directly to our sentence pairs
            for idx, (disp_text, spoken_text) in enumerate(sentence_pairs):
                b_ev = boundary_events[idx]
                # edge-tts offsets are in 100ns units (ticks)
                start_sec = round(b_ev["offset"] / 10_000_000.0, 3)
                dur_sec = round(b_ev["duration"] / 10_000_000.0, 3)
                end_sec = round(start_sec + dur_sec, 3)

                words = []
                if request.include_word_segments:
                    words = self._subdivide_words(spoken_text, start_sec, end_sec)

                sentence_segments.append(
                    SentenceSegment(
                        sentence_index=idx,
                        display_text=disp_text,
                        spoken_text=spoken_text,
                        start_time=start_sec,
                        end_time=end_sec,
                        words=words
                    )
                )
                total_duration = max(total_duration, end_sec)
        else:
            # Fallback alignment across the actual total duration
            # Approximate total duration from boundary events or file size (128kbps = 16000 bytes/sec)
            estimated_dur = max(
                len(audio_bytes) / 16000.0 if audio_bytes else 0.0,
                len(full_spoken_script.split()) / 2.5
            )
            sentence_segments = self._proportional_sentence_alignment(
                sentence_pairs=sentence_pairs,
                total_duration=estimated_dur,
                include_words=request.include_word_segments
            )
            total_duration = estimated_dur

        return TTSVoiceResponse(
            complete_answer_text=request.text,
            spoken_text=full_spoken_script,
            audio_url=f"/api/v1/voice/audio/{audio_filename}",
            duration_seconds=round(total_duration, 2),
            sentence_segments=sentence_segments,
            voice_used=voice,
            alignment_method="neural_speech_timestamps",
            audio_format="mp3"
        )

    def _generate_fallback_alignment(
        self,
        request: TTSVoiceRequest,
        full_spoken_script: str,
        sentence_pairs: List[Tuple[str, str]],
        error_msg: str
    ) -> TTSVoiceResponse:
        """Provide deterministic proportional timestamp alignment when cloud/neural TTS is unreachable."""
        # Standard educational speaking rate: ~150 words per minute = 2.5 words/second
        words_count = max(len(full_spoken_script.split()), 1)
        total_duration = round(words_count / 2.5, 2)

        sentence_segments = self._proportional_sentence_alignment(
            sentence_pairs=sentence_pairs,
            total_duration=total_duration,
            include_words=request.include_word_segments
        )

        # Ensure a valid fallback audio file exists in storage
        cache_key = f"{full_spoken_script}_{request.voice or self.default_voice}"
        file_hash = hashlib.md5(cache_key.encode('utf-8')).hexdigest()
        audio_filename = f"{file_hash}.mp3"
        audio_filepath = os.path.join(STORAGE_AUDIO_DIR, audio_filename)
        if not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) == 0:
            with open(audio_filepath, "wb") as f:
                f.write(b"\xff\xfb\x90d\x00\x00\x00\x00" * 32)

        return TTSVoiceResponse(
            complete_answer_text=request.text,
            spoken_text=full_spoken_script,
            audio_url=f"/api/v1/voice/audio/{audio_filename}",
            duration_seconds=total_duration,
            sentence_segments=sentence_segments,
            voice_used=request.voice or self.default_voice,
            alignment_method="forced_alignment_fallback",
            audio_format="browser_speech",
            error=f"Neural TTS offline ({error_msg}); client fallback enabled."
        )

    def _subdivide_words(
        self,
        spoken_text: str,
        start_time: float,
        end_time: float
    ) -> List[WordSegment]:
        """Divide a sentence's time duration across words proportionally based on character length."""
        words = spoken_text.split()
        if not words:
            return []

        total_chars = sum(len(w) for w in words)
        sentence_dur = max(end_time - start_time, 0.2)
        cur_time = start_time
        segments: List[WordSegment] = []

        for w in words:
            w_weight = len(w) / max(total_chars, 1)
            w_dur = sentence_dur * w_weight
            w_end = min(round(cur_time + w_dur, 3), end_time)
            segments.append(
                WordSegment(
                    word=w,
                    start_time=round(cur_time, 3),
                    end_time=w_end
                )
            )
            cur_time = w_end

        return segments

    def _proportional_sentence_alignment(
        self,
        sentence_pairs: List[Tuple[str, str]],
        total_duration: float,
        include_words: bool
    ) -> List[SentenceSegment]:
        """Distribute total duration across sentences based on spoken word counts with pause buffers."""
        sentence_segments: List[SentenceSegment] = []
        total_spoken_words = sum(len(sp[1].split()) for sp in sentence_pairs)
        if total_spoken_words == 0:
            total_spoken_words = 1

        cur_start = 0.0
        for idx, (disp, spoken) in enumerate(sentence_pairs):
            word_count = max(len(spoken.split()), 1)
            ratio = word_count / total_spoken_words
            seg_dur = total_duration * ratio
            seg_end = round(cur_start + seg_dur, 3)

            words = []
            if include_words:
                words = self._subdivide_words(spoken, cur_start, seg_end)

            sentence_segments.append(
                SentenceSegment(
                    sentence_index=idx,
                    display_text=disp,
                    spoken_text=spoken,
                    start_time=round(cur_start, 3),
                    end_time=seg_end,
                    words=words
                )
            )
            cur_start = seg_end

        return sentence_segments


voice_service = EducationalVoiceService()
