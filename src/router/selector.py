from __future__ import annotations

from typing import Dict, List


def select_top_k(ranked: List[Dict], k: int = 1) -> List[Dict]:
    if k <= 0:
        return []
    return ranked[:k]


def select_for_task(ranked: List[Dict], task_type: str = "simple") -> List[Dict]:
    # v1 policy: simple -> top1, composite -> top3
    if task_type == "composite":
        return select_top_k(ranked, 3)
    return select_top_k(ranked, 1)
