from __future__ import annotations

from typing import Dict, List, Protocol


class VectorBackend(Protocol):
    def similarity(self, query: str, documents: List[str]) -> List[float]:
        ...


class NullVectorBackend:
    """Fallback backend when vector search is unavailable."""

    def similarity(self, query: str, documents: List[str]) -> List[float]:
        return [0.0 for _ in documents]


class KeywordVectorBackend:
    """Simple local fallback: keyword overlap ratio (deterministic, cheap)."""

    def similarity(self, query: str, documents: List[str]) -> List[float]:
        q_tokens = {t for t in query.lower().split() if t}
        scores: List[float] = []
        for d in documents:
            d_tokens = {t for t in d.lower().split() if t}
            if not q_tokens or not d_tokens:
                scores.append(0.0)
                continue
            inter = len(q_tokens & d_tokens)
            union = len(q_tokens | d_tokens)
            scores.append(round(inter / union, 6) if union else 0.0)
        return scores


class MultilingualEmbeddingBackend:
    """Semantic similarity using paraphrase-multilingual-MiniLM-L12-v2.

    Supports Korean and English out of the box.
    Falls back to KeywordVectorBackend if sentence-transformers is not installed.
    Model is loaded once at instantiation and cached for the process lifetime.
    """

    _model = None  # class-level cache

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._ensure_model()

    def _ensure_model(self) -> None:
        if MultilingualEmbeddingBackend._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            MultilingualEmbeddingBackend._model = SentenceTransformer(self.model_name)
        except ImportError:
            MultilingualEmbeddingBackend._model = None

    def similarity(self, query: str, documents: List[str]) -> List[float]:
        if MultilingualEmbeddingBackend._model is None:
            return KeywordVectorBackend().similarity(query, documents)

        import numpy as np
        model = MultilingualEmbeddingBackend._model
        q_emb = model.encode(query, convert_to_numpy=True)
        d_embs = model.encode(documents, convert_to_numpy=True)

        # cosine similarity
        q_norm = q_emb / (np.linalg.norm(q_emb) + 1e-10)
        d_norms = d_embs / (np.linalg.norm(d_embs, axis=1, keepdims=True) + 1e-10)
        scores = (d_norms @ q_norm).tolist()
        return [round(float(s), 6) for s in scores]


def get_default_backend() -> VectorBackend:
    """Return MultilingualEmbeddingBackend if available, else KeywordVectorBackend."""
    try:
        import sentence_transformers  # noqa: F401
        return MultilingualEmbeddingBackend()
    except ImportError:
        return KeywordVectorBackend()


def compute_vector_scores(
    query: str,
    skill_docs: Dict[str, str],
    backend: VectorBackend | None = None,
) -> Dict[str, float]:
    backend = backend or NullVectorBackend()
    ids = list(skill_docs.keys())
    docs = [skill_docs[i] for i in ids]
    try:
        values = backend.similarity(query, docs)
    except Exception:
        values = [0.0 for _ in docs]
    return {sid: float(v) for sid, v in zip(ids, values)}
