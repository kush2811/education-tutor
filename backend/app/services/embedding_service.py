"""Embedding generation service supporting Gemini text-embedding-004 and local deterministic semantic embeddings."""

import math
import hashlib
from typing import List, Optional
import numpy as np
from app.core.config import settings
from app.core.logging import logger

EMBEDDING_DIM = 768


class EmbeddingService:
    """Generates normalized vector embeddings for educational documents and student queries."""

    def __init__(self):
        self.dim = EMBEDDING_DIM
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("EmbeddingService initialized with Google Gemini text-embedding-004.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client for embeddings: {e}. Falling back to local semantic embeddings.")

    def embed_text(self, text: str) -> List[float]:
        """Generate a single 768-dimensional normalized embedding vector."""
        if not text or not text.strip():
            return [0.0] * self.dim

        # 1. Try Gemini cloud embedding if client available
        if self._gemini_client:
            try:
                response = self._gemini_client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                if response.embedding and response.embedding.values:
                    vec = list(response.embedding.values)
                    # Normalize vector
                    arr = np.array(vec, dtype=np.float32)
                    norm = np.linalg.norm(arr)
                    if norm > 0:
                        arr = arr / norm
                    return arr.tolist()
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed: {e}. Using deterministic local embedding fallback.")

        # 2. Deterministic local semantic embedding fallback
        return self._generate_local_embedding(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized vector embeddings for a list of text strings."""
        return [self.embed_text(t) for t in texts]

    def _generate_local_embedding(self, text: str) -> List[float]:
        """High-resolution feature hashing and n-gram semantic projection into a normalized 768-dim space."""
        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        # Word unigrams and bigrams
        tokens = list(words)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")

        for idx, token in enumerate(tokens):
            # Positional decay weight
            weight = 1.0 / (1.0 + 0.005 * idx)
            # Hash token to primary bucket
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            bucket1 = h % self.dim
            sign1 = 1.0 if ((h >> 8) & 1) == 0 else -1.0
            vec[bucket1] += sign1 * weight

            # Secondary projection for character trigrams
            if len(token) >= 3:
                for c_idx in range(len(token) - 2):
                    trigram = token[c_idx:c_idx+3]
                    h_tri = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
                    bucket_tri = h_tri % self.dim
                    sign_tri = 1.0 if ((h_tri >> 4) & 1) == 0 else -1.0
                    vec[bucket_tri] += sign_tri * 0.3 * weight

        # L2 Normalization
        norm = np.linalg.norm(vec)
        if norm > 1e-9:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()


embedding_service = EmbeddingService()

