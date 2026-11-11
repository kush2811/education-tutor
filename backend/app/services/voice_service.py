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
from app.core.config import settings
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

        # 2. Attempt Neural TTS with edge-tts (fast timeout in testing, 15s for longer explanations in prod)
        tts_timeout = 4.0 if settings.ENVIRONMENT == "testing" else 15.0
        try:
            return await asyncio.wait_for(
                self._generate_with_edge_tts(
                    request=request,
                    full_spoken_script=full_spoken_script,
                    sentence_pairs=sentence_pairs
                ),
                timeout=tts_timeout
            )
        except Exception as e:
            logger.warning(f"Neural Edge-TTS generation failed or timed out ({e}); falling back to client-aligned speech.")
            return self._generate_fallback_alignment(
                request=request,
                full_spoken_script=full_spoken_script,
                sentence_pairs=sentence_pairs,
                error_msg=str(e)
            )

    @staticmethod
    def _clean_display_line(disp: str) -> str:
        """Strip raw markdown prefixes while keeping readable display text."""
        cleaned = re.sub(r'^#+\s*', '', disp.strip())
        cleaned = re.sub(r'^>\s*', '', cleaned)
        cleaned = re.sub(r'^\s*[\*\-]\s+', '', cleaned)
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        return cleaned.strip() or disp.strip()

    @staticmethod
    def _align_word_boundaries(
        sentence_pairs: List[Tuple[str, str]],
        word_events: List[Dict[str, Any]],
        include_words: bool,
    ) -> Tuple[List[SentenceSegment], float]:
        """Align Edge-TTS WordBoundary events to sentence_pairs token-by-token to prevent line drift."""
        def _norm(tok: str) -> str:
            return re.sub(r'[^a-z0-9]', '', tok.lower())

        # Expand any multi-word WordBoundary chunks (e.g., "90 degrees", "3 squared") into individual word events
        expanded_events: List[Dict[str, Any]] = []
        for ev in word_events:
            parts = ev.get("text", "").split()
            if len(parts) <= 1:
                expanded_events.append(ev)
            else:
                sub_dur = max(ev.get("duration", 0) // len(parts), 1)
                for p_i, part in enumerate(parts):
                    expanded_events.append({
                        "text": part,
                        "offset": ev["offset"] + p_i * sub_dur,
                        "duration": sub_dur,
                    })
        word_events = expanded_events

        segments: List[SentenceSegment] = []
        cursor = 0
        last_end = 0.0
        total_evs = len(word_events)
        total_alnum_words = sum(
            1 for _, sp in sentence_pairs for tok in sp.split() if _norm(tok)
        )
        exact_bijection = (total_alnum_words == total_evs)

        for idx, (disp_text, spoken_text) in enumerate(sentence_pairs):
            raw_words = spoken_text.split()
            word_segments: List[WordSegment] = []
            sent_start: Optional[float] = None
            sent_end: float = last_end

            for w in raw_words:
                w_norm = _norm(w)
                if not w_norm or cursor >= total_evs:
                    continue

                match_idx = cursor
                if not exact_bijection:
                    cur_norm = _norm(word_events[cursor].get("text", ""))
                    if cur_norm != w_norm and len(w_norm) >= 3:
                        for probe in range(cursor + 1, min(cursor + 4, total_evs)):
                            if _norm(word_events[probe].get("text", "")) == w_norm:
                                match_idx = probe
                                break

                ev = word_events[match_idx]
                w_start = round(ev["offset"] / 10_000_000.0, 3)
                w_end = round((ev["offset"] + ev["duration"]) / 10_000_000.0, 3)
                cursor = match_idx + 1

                if not exact_bijection:
                    accum_norm = _norm(ev.get("text", ""))
                    while accum_norm and len(accum_norm) < len(w_norm) and cursor < total_evs:
                        next_ev = word_events[cursor]
                        next_norm = _norm(next_ev.get("text", ""))
                        if next_norm and (accum_norm + next_norm) in w_norm:
                            accum_norm += next_norm
                            w_end = round((next_ev["offset"] + next_ev["duration"]) / 10_000_000.0, 3)
                            cursor += 1
                        else:
                            break

                w_end = max(w_end, round(w_start + 0.04, 3))
                if sent_start is None:
                    sent_start = w_start
                sent_end = max(sent_end, w_end)

                if include_words:
                    word_segments.append(
                        WordSegment(word=w, start_time=w_start, end_time=w_end)
                    )

            if sent_start is None:
                sent_start = last_end
                sent_end = round(last_end + max(len(raw_words) * 0.35, 0.3), 3)
                if include_words:
                    word_segments = EducationalVoiceService._subdivide_words(spoken_text, sent_start, sent_end)

            sent_end = max(sent_end, round(sent_start + 0.1, 3))
            last_end = sent_end

            segments.append(
                SentenceSegment(
                    sentence_index=idx,
                    display_text=EducationalVoiceService._clean_display_line(disp_text),
                    spoken_text=spoken_text,
                    start_time=sent_start,
                    end_time=sent_end,
                    words=word_segments,
                )
            )

        return segments, last_end

    async def _generate_with_edge_tts(
        self,
        request: TTSVoiceRequest,
        full_spoken_script: str,
        sentence_pairs: List[Tuple[str, str]]
    ) -> TTSVoiceResponse:
        """Call edge-tts with WordBoundary events and map exact neural timestamps to sentences and words."""
        import edge_tts

        voice = request.voice or self.default_voice
        rate = request.rate or "+0%"
        pitch = request.pitch or "+0Hz"

        cache_key = f"wb_{full_spoken_script}_{voice}_{rate}_{pitch}"
        file_hash = hashlib.md5(cache_key.encode('utf-8')).hexdigest()
        audio_filename = f"{file_hash}.mp3"
        audio_filepath = os.path.join(STORAGE_AUDIO_DIR, audio_filename)

        audio_bytes = bytearray()
        word_events: List[Dict[str, Any]] = []

        comm = edge_tts.Communicate(
            text=full_spoken_script,
            voice=voice,
            rate=rate,
            pitch=pitch,
            boundary="WordBoundary",
        )

        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                audio_bytes.extend(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_events.append(chunk)

        if audio_bytes and (not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) == 0):
            with open(audio_filepath, "wb") as f:
                f.write(audio_bytes)

        if word_events:
            sentence_segments, total_duration = self._align_word_boundaries(
                sentence_pairs=sentence_pairs,
                word_events=word_events,
                include_words=request.include_word_segments,
            )
        else:
            # Edge-TTS uses 48 kbps (~6000 bytes/sec) MP3 encoding
            estimated_dur = max(
                len(audio_bytes) / 6000.0 if audio_bytes else 0.0,
                len(full_spoken_script.split()) / 2.5
            )
            cleaned_pairs = [(self._clean_display_line(d), s) for d, s in sentence_pairs]
            sentence_segments = self._proportional_sentence_alignment(
                sentence_pairs=cleaned_pairs,
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

        cleaned_pairs = [(self._clean_display_line(d), s) for d, s in sentence_pairs]
        sentence_segments = self._proportional_sentence_alignment(
            sentence_pairs=cleaned_pairs,
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

    @staticmethod
    def _subdivide_words(
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
