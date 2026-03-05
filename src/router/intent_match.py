from __future__ import annotations

import re
from typing import Dict, Iterable


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r'[^a-zA-Z0-9가-힣_\-]+', text.lower()) if t}


def compute_intent_match(user_intent: str, skill: Dict) -> float:
    q = _tokens(user_intent)
    if not q:
        return 0.0

    fields: list[str] = []
    fields.append(str(skill.get('skill_id', '')))
    fields.append(str(skill.get('domain', '')))
    fields.extend(skill.get('intents', []) or [])

    s_tokens = _tokens(' '.join(fields))
    if not s_tokens:
        return 0.0

    inter = len(q & s_tokens)
    union = len(q | s_tokens)
    base = (inter / union) if union else 0.0

    # small boosts for exact phrase hits in skill_id/intents
    skill_id = str(skill.get('skill_id', '')).lower()
    boosts = 0.0
    for tok in q:
        if tok in skill_id:
            boosts += 0.03
    for it in (skill.get('intents', []) or []):
        il = str(it).lower()
        if any(tok in il for tok in q):
            boosts += 0.05

    return min(1.0, round(base + boosts, 6))
