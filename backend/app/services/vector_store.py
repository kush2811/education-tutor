"""Vector storage interface using ChromaDB for educational curriculum knowledge chunks."""

import os
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.educational_chunker import EducationalChunk

COLLECTION_NAME = "educational_curriculum"


class ChromaVectorStore:
    """Manages persistent curriculum vector embeddings, metadata indexing, and similarity search."""

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_dir = persist_directory or settings.VECTOR_STORE_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = None
        self._collection = None
        self._init_collection()

    def _init_collection(self):
        """Initialize ChromaDB persistent client and retrieve/create collection."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            # Create or get collection with cosine distance
            self._collection = self._client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB initialized at '{self.persist_dir}' with collection '{COLLECTION_NAME}'. Total count: {self._collection.count()}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB at '{self.persist_dir}': {e}")
            raise e

    def add_chunks(
        self,
        chunks: List[EducationalChunk],
        embeddings: List[List[float]],
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Insert educational chunks and their vector embeddings into ChromaDB."""
        if not chunks:
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chk in chunks:
            ids.append(chk.chunk_id)
            documents.append(chk.content)

            meta = dict(chk.metadata)
            if additional_metadata:
                meta.update(additional_metadata)
            # Chroma requires metadata values to be string, int, float, or bool
            sanitized_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    sanitized_meta[k] = v
                elif v is None:
                    sanitized_meta[k] = ""
                else:
                    sanitized_meta[k] = str(v)
            metadatas.append(sanitized_meta)

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(ids)} chunks to ChromaDB collection '{COLLECTION_NAME}'.")
        return len(ids)

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search ChromaDB for top-K nearest curriculum chunks with optional metadata filtering."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        matches: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return matches

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for i in range(len(ids)):
            # Cosine distance in Chroma: 0 = identical, 2 = opposite
            # Similarity score = 1 - (distance / 2)
            dist = distances[i] if distances else 0.0
            similarity = max(0.0, 1.0 - (dist / 2.0))
            matches.append({
                "chunk_id": ids[i],
                "content": docs[i],
                "metadata": metas[i],
                "similarity": similarity,
                "distance": dist
            })

        return matches

    def delete_document(self, document_id: str) -> int:
        """Remove all chunks associated with a specific document ID."""
        try:
            # Query chunks belonging to document
            result = self._collection.get(
                where={"document_id": document_id}
            )
            if result and result["ids"]:
                chunk_ids = result["ids"]
                self._collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for document '{document_id}' from ChromaDB.")
                return len(chunk_ids)
            return 0
        except Exception as e:
            logger.warning(f"Error deleting chunks for document '{document_id}': {e}")
            return 0

    def count(self) -> int:
        """Return total number of vectors in collection."""
        return self._collection.count()


vector_store = ChromaVectorStore()
