import json
import logging
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class LocalHybridSearch:
    """Simple local TF-IDF retriever as a stand-in for vector + keyword search."""

    def __init__(self, corpus_path: str):
        self.corpus_path = Path(corpus_path)
        self.docs = self._load_docs()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        if self.docs:
            self.matrix = self.vectorizer.fit_transform([d["text"] for d in self.docs])
        else:
            self.matrix = None

    def _load_docs(self) -> list[dict[str, Any]]:
        docs = []
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

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if self.matrix is None:
            return []
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix).flatten()
        ranked = scores.argsort()[::-1][:top_k]
        return [{**self.docs[i], "score": float(scores[i])} for i in ranked]
