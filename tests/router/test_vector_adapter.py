from src.router.vector_adapter import (
    KeywordVectorBackend,
    NullVectorBackend,
    compute_vector_scores,
)


def test_null_backend_returns_zero():
    scores = compute_vector_scores("debug api", {"a": "python api", "b": "frontend"}, NullVectorBackend())
    assert scores["a"] == 0.0
    assert scores["b"] == 0.0


def test_keyword_backend_scores_overlap():
    backend = KeywordVectorBackend()
    scores = compute_vector_scores(
        "python api debug",
        {
            "a": "python api service",
            "b": "react ui component",
        },
        backend,
    )
    assert scores["a"] > scores["b"]
    assert 0.0 <= scores["a"] <= 1.0
