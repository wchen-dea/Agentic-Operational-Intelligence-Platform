import tempfile

from ai_layer.rag.retrieval.hybrid_search import LocalHybridSearch


def test_hybrid_search_valid_corpus():
    from config.settings import settings
    search = LocalHybridSearch(settings.rag_corpus_path)
    results = search.search("promotion strategy", top_k=2)
    assert len(results) > 0
    assert "title" in results[0]
    assert "score" in results[0]


def test_hybrid_search_missing_corpus():
    search = LocalHybridSearch("/nonexistent/path/corpus.jsonl")
    assert search.docs == []
    assert search.matrix is None
    results = search.search("anything")
    assert results == []


def test_hybrid_search_empty_corpus():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("")
        f.flush()
        search = LocalHybridSearch(f.name)
    assert search.docs == []
    assert search.matrix is None
    assert search.search("test") == []
