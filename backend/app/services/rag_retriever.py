"""Hybrid retrieval (Dense Semantic + BM25 Sparse), Reciprocal Rank Fusion, and Reranking."""

import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from rank_bm25 import BM25Okapi

from app.core.logging import logger
from app.models.knowledge import DocumentChunk, EducationalSource, KnowledgeDocument
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.schemas.rag import RetrievedChunkItem


class EducationalRAGRetriever:
    """Orchestrates hybrid retrieval and reranking across the curriculum knowledge base."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        db: Session,
        subject: Optional[str] = None,
        academic_level: Optional[str] = None,
        source_id: Optional[str] = None,
        top_k: int = 5,
        enable_hybrid: bool = True,
        enable_reranking: bool = True,
        confidence_threshold: float = 0.25
    ) -> List[RetrievedChunkItem]:
        """Execute hybrid search, Reciprocal Rank Fusion (RRF), and cross-encoder reranking."""
        dense_candidates: List[Dict[str, Any]] = []
        bm25_candidates: List[Dict[str, Any]] = []

        # Build metadata filter for ChromaDB
        where_filter: Dict[str, Any] = {}
        if subject:
            where_filter["subject"] = subject
        if academic_level:
            where_filter["academic_level"] = academic_level
        if source_id:
            where_filter["source_id"] = source_id
        filter_arg = where_filter if where_filter else None

        # 1. Dense Semantic Retrieval
        query_vec = embedding_service.embed_text(query)
        dense_matches = vector_store.query(
            query_embedding=query_vec,
            top_k=max(top_k * 3, 10),
            where_filter=filter_arg
        )
        for rank, m in enumerate(dense_matches):
            dense_candidates.append({
                "chunk_id": m["chunk_id"],
                "content": m["content"],
                "metadata": m["metadata"],
                "dense_score": float(m["similarity"]),
                "dense_rank": rank + 1
            })

        # 2. Sparse BM25 Keyword Retrieval
        if enable_hybrid:
            bm25_matches = self._search_bm25(
                query=query,
                db=db,
                subject=subject,
                source_id=source_id,
                top_k=max(top_k * 3, 10)
            )
            for rank, m in enumerate(bm25_matches):
                bm25_candidates.append({
                    "chunk_id": m["chunk_id"],
                    "content": m["content"],
                    "metadata": m["metadata"],
                    "bm25_score": float(m["score"]),
                    "bm25_rank": rank + 1
                })

        # 3. Reciprocal Rank Fusion (RRF)
        fused_pool: Dict[str, Dict[str, Any]] = {}

        for item in dense_candidates:
            cid = item["chunk_id"]
            rrf_score = 1.0 / (self.rrf_k + item["dense_rank"])
            fused_pool[cid] = {
                "chunk_id": cid,
                "content": item["content"],
                "metadata": item["metadata"],
                "dense_score": item["dense_score"],
                "bm25_score": 0.0,
                "rrf_score": rrf_score
            }

        for item in bm25_candidates:
            cid = item["chunk_id"]
            rrf_contrib = 1.0 / (self.rrf_k + item["bm25_rank"])
            if cid in fused_pool:
                fused_pool[cid]["rrf_score"] += rrf_contrib
                fused_pool[cid]["bm25_score"] = item["bm25_score"]
            else:
                fused_pool[cid] = {
                    "chunk_id": cid,
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "dense_score": 0.0,
                    "bm25_score": item["bm25_score"],
                    "rrf_score": rrf_contrib
                }

        # 4. Reranking & Confidence Scoring
        reranked: List[RetrievedChunkItem] = []
        query_terms = set(query.lower().split())

        for cid, data in fused_pool.items():
            meta = data["metadata"]
            dense_s = data["dense_score"]
            bm25_s = data["bm25_score"]

            # Reranker scoring heuristics:
            # - Dense semantic weight: 40%
            # - BM25 / lexical match: 30%
            # - Heading match bonus: 15% if query words appear in chapter or section
            heading_bonus = 0.0
            heading_text = f"{meta.get('chapter', '')} {meta.get('section', '')}".lower()
            if any(t in heading_text for t in query_terms if len(t) > 3):
                heading_bonus = 0.15

            # - Math symbol bonus: 15% if query references equations and chunk contains math
            chunk_rec = db.query(DocumentChunk).filter(DocumentChunk.id == cid).first()
            math_exprs = chunk_rec.extracted_math if chunk_rec and chunk_rec.extracted_math else []
            math_bonus = 0.15 if (math_exprs and any(c in query for c in ["=", "+", "-", "^", "\\", "x", "y"])) else 0.0

            if enable_reranking:
                rerank_score = (dense_s * 0.40) + (bm25_s * 0.30) + heading_bonus + math_bonus
            else:
                rerank_score = max(dense_s, bm25_s)

            # Look up source information
            source_rec = db.query(EducationalSource).filter(EducationalSource.id == meta.get("source_id")).first()
            source_url = source_rec.source_url if source_rec else "https://ncert.nic.in"
            authority = source_rec.source_authority if source_rec else meta.get("source_authority", "Educational Authority")
            license_type = source_rec.license_type if source_rec else meta.get("license_type", "Educational Use")
            source_name = source_rec.source_name if source_rec else meta.get("source_name", "Curriculum Source")

            # Check threshold
            if rerank_score >= confidence_threshold:
                reranked.append(RetrievedChunkItem(
                    chunk_id=cid,
                    document_id=meta.get("document_id", ""),
                    source_id=meta.get("source_id", ""),
                    source_name=source_name,
                    source_url=source_url,
                    authority=authority,
                    license_type=license_type,
                    chapter=meta.get("chapter"),
                    section=meta.get("section"),
                    page_number=int(meta.get("page_number", 1)),
                    content=data["content"],
                    extracted_math=math_exprs,
                    dense_score=round(dense_s, 4),
                    bm25_score=round(bm25_s, 4),
                    combined_score=round(data["rrf_score"], 4),
                    rerank_score=round(rerank_score, 4)
                ))

        # Sort by rerank score descending and slice to top_k
        reranked.sort(key=lambda x: x.rerank_score, reverse=True)
        return reranked[:top_k]

    def _search_bm25(
        self,
        query: str,
        db: Session,
        subject: Optional[str] = None,
        source_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform sparse BM25 scoring over indexed document chunks in database."""
        chunk_query = db.query(DocumentChunk)
        if source_id:
            chunk_query = chunk_query.filter(DocumentChunk.source_id == source_id)

        chunks = chunk_query.all()
        if not chunks:
            return []

        # Filter by subject if specified
        if subject:
            filtered_chunks = []
            for chk in chunks:
                if chk.document and chk.document.source and subject.lower() in chk.document.source.subject.lower():
                    filtered_chunks.append(chk)
            if filtered_chunks:
                chunks = filtered_chunks

        # Tokenize corpus
        corpus_texts = [c.content for c in chunks]
        tokenized_corpus = [c.lower().split() for c in corpus_texts]

        bm25 = BM25Okapi(tokenized_corpus)
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)

        # Normalize BM25 scores to [0, 1]
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0

        matches = []
        for i, score in enumerate(scores):
            if score > 0:
                chk = chunks[i]
                norm_score = min(1.0, score / max_score)
                meta = {
                    "document_id": chk.document_id,
                    "source_id": chk.source_id,
                    "chapter": chk.chapter,
                    "section": chk.section,
                    "page_number": chk.page_number
                }
                matches.append({
                    "chunk_id": chk.id,
                    "content": chk.content,
                    "metadata": meta,
                    "score": norm_score
                })

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:top_k]


rag_retriever = EducationalRAGRetriever()
