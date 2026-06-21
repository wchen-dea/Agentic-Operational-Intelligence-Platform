"""Hybrid retrieval — combines ChromaDB vector search with TF-IDF keyword search.

Falls back to TF-IDF-only when ChromaDB is not available or the collection
is empty.  Uses ChromaDB's built-in default embedding function.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ChromaDB lazy init — optional at import time
# ---------------------------------------------------------------------------

_chroma_available = False
try:
    import chromadb  # noqa: F401

    _chroma_available = True
except ImportError:
    pass


class LocalHybridSearch:
    """Hybrid retriever that merges dense (ChromaDB) and sparse (TF-IDF) results.

    On construction the JSONL corpus is loaded into both a ChromaDB ephemeral
    collection (for semantic / embedding search) and a TF-IDF matrix (for
    keyword search).  At query time both result sets are merged via reciprocal
    rank fusion.
    """

    def __init__(self, corpus_path: str) -> None:
        self.corpus_path = Path(corpus_path)
        self.docs = self._load_docs()

        # Sparse (TF-IDF)
        self.vectorizer = TfidfVectorizer(stop_words="english")
        if self.docs:
            self.tfidf_matrix = self.vectorizer.fit_transform(
                [d["text"] for d in self.docs]
            )
        else:
            self.tfidf_matrix = None

        # Dense (ChromaDB)
        self._collection: Any = None
        if _chroma_available and self.docs:
            self._init_chroma()

    # ------------------------------------------------------------------
    # Backward-compatible property
    # ------------------------------------------------------------------

    @property
    def matrix(self) -> Any:
        return self.tfidf_matrix

    # ------------------------------------------------------------------
    # Corpus loading
    # ------------------------------------------------------------------

    def _load_docs(self) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        if not self.corpus_path.exists():
            logger.error("RAG corpus not found at %s", self.corpus_path)
            return docs
        with self.corpus_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    docs.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning("Skipping malformed JSON on line %d: %s", line_num, e)
        return docs

    # ------------------------------------------------------------------
    # ChromaDB
    # ------------------------------------------------------------------

    def _init_chroma(self) -> None:
        try:
            client = chromadb.Client()  # ephemeral in-process
            self._collection = client.get_or_create_collection(
                name="rag_corpus",
                metadata={"hnsw:space": "cosine"},
            )
            # Upsert all documents (idempotent by ID)
            ids = [d.get("id", str(i)) for i, d in enumerate(self.docs)]
            documents = [d["text"] for d in self.docs]
            metadatas = [
                {
                    k: (json.dumps(v) if isinstance(v, list) else str(v))
                    for k, v in d.items()
                    if k not in ("text",) and v is not None
                }
                for d in self.docs
            ]
            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(
                "ChromaDB collection loaded with %d documents", len(self.docs)
            )
        except Exception as exc:
            logger.warning("ChromaDB init failed, using TF-IDF only: %s", exc)
            self._collection = None

    # ------------------------------------------------------------------
    # Search methods
    # ------------------------------------------------------------------

    def _tfidf_search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Return (doc_index, score) pairs from TF-IDF search."""
        if self.tfidf_matrix is None:
            return []
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.tfidf_matrix).flatten()
        ranked = scores.argsort()[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in ranked]

    def _chroma_search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Return (doc_index, score) pairs from ChromaDB vector search."""
        if self._collection is None:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(top_k, len(self.docs)),
            )
            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            # Map IDs back to doc indices
            id_to_idx = {
                d.get("id", str(i)): i for i, d in enumerate(self.docs)
            }
            pairs: list[tuple[int, float]] = []
            for doc_id, dist in zip(ids, distances):
                idx = id_to_idx.get(doc_id)
                if idx is not None:
                    # ChromaDB cosine distance → similarity
                    score = max(0.0, 1.0 - dist)
                    pairs.append((idx, score))
            return pairs
        except Exception as exc:
            logger.warning("ChromaDB query failed: %s", exc)
            return []

    @staticmethod
    def _reciprocal_rank_fusion(
        *ranked_lists: list[tuple[int, float]],
        k: int = 60,
    ) -> list[tuple[int, float]]:
        """Merge multiple ranked lists via reciprocal rank fusion (RRF)."""
        scores: dict[int, float] = {}
        for ranked in ranked_lists:
            for rank, (idx, _score) in enumerate(ranked):
                scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return fused

    def search(
        self,
        query: str,
        top_k: int = 3,
        domain: str | None = None,
        persona: str | None = None,
    ) -> list[dict[str, Any]]:
        """Run hybrid search: merge TF-IDF + ChromaDB results via RRF.

        Args:
            query: Natural language search query.
            top_k: Max results to return.
            domain: Optional domain filter (e.g. "promotion", "work_order").
            persona: Optional persona filter (e.g. "store_manager", "executive").
        """
        if not self.docs:
            return []

        # Fetch from both engines
        tfidf_results = self._tfidf_search(query, top_k=top_k * 2)
        chroma_results = self._chroma_search(query, top_k=top_k * 2)

        # Fuse
        if chroma_results:
            fused = self._reciprocal_rank_fusion(tfidf_results, chroma_results)
        else:
            fused = tfidf_results

        # Build result docs with metadata filtering
        results: list[dict[str, Any]] = []
        for idx, score in fused:
            doc = self.docs[idx]
            if domain and doc.get("domain") != domain:
                continue
            if persona and persona not in doc.get("persona", []):
                continue
            results.append({**doc, "score": float(score)})
            if len(results) >= top_k:
                break

        return results
