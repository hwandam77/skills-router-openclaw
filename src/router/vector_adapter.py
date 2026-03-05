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
