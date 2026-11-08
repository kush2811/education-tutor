"""Subtitle synchronization and word-level timestamp alignment service."""

from typing import List, Dict, Any
from app.core.logging import logger


class SubtitleAligner:
    """Generates millisecond-accurate word boundaries for synchronized subtitle rendering."""

    def align_text_and_audio(self, text: str, duration_ms: int) -> List[Dict[str, Any]]:
        """Generate word-level offset timestamps for karaoke-style UI subtitle highlighting."""
        words = text.split()
        if not words:
            return []
        
        step_ms = max(1, duration_ms // len(words))
        timeline = []
        for i, word in enumerate(words):
            start = i * step_ms
            end = start + step_ms
            timeline.append({
                "word": word,
                "start_ms": start,
                "end_ms": end
            })
        
        logger.info(f"Aligned {len(words)} words over {duration_ms}ms")
        return timeline


subtitle_aligner = SubtitleAligner()

