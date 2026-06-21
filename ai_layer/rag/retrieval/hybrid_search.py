from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LocalHybridSearch:
    """Simple local TF-IDF retriever as a stand-in for vector + keyword search."""

    def __init__(self, corpus_path: str):
        self.corpus_path = Path(corpus_path)
        self.docs = self._load_docs()
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform([d["text"] for d in self.docs])

    def _load_docs(self) -> List[Dict[str, Any]]:
        docs = []
        with self.corpus_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    docs.append(json.loads(line))
        return docs

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        q = self.vectorizer.transform([query])
        scores = cosine_similarity(q, self.matrix).flatten()
        ranked = scores.argsort()[::-1][:top_k]
        return [{**self.docs[i], "score": float(scores[i])} for i in ranked]
