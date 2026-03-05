from __future__ import annotations

from copy import deepcopy
from typing import Dict, List

DEFAULTS = {
    "status": "active",
    "domain": "general",
    "intents": [],
    "risk_level": "low",
    "required_tools": [],
    "latency_class": "normal",
    "cost_class": "normal",
    "conflicts": [],
    "dependencies": [],
    "quality_score": 0.5,
}


def enrich_skills(skills: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for s in skills:
        e = deepcopy(s)
        for k, v in DEFAULTS.items():
            e.setdefault(k, v)
        # simple deprecation heuristic
        sid = str(e.get("skill_id", "")).lower()
        if "legacy" in sid and e.get("status") == "active":
            e["status"] = "deprecated"
        out.append(e)
    return out
