from __future__ import annotations

from typing import Dict, List, Tuple

REQUIRED_FIELDS = {
    "skill_id": str,
    "version": str,
    "status": str,
    "domain": str,
    "intents": list,
    "risk_level": str,
    "required_tools": list,
    "latency_class": str,
    "cost_class": str,
    "conflicts": list,
    "dependencies": list,
    "quality_score": (float, int),
}

ENUMS = {
    "status": {"active", "deprecated", "experimental"},
    "risk_level": {"low", "medium", "high"},
    "latency_class": {"fast", "normal", "slow"},
    "cost_class": {"low", "normal", "high"},
}


def validate_skill(skill: Dict) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    for field, typ in REQUIRED_FIELDS.items():
        if field not in skill:
            errors.append(f"missing:{field}")
            continue
        if not isinstance(skill[field], typ):
            errors.append(f"type:{field}")
    for field, allowed in ENUMS.items():
        if field in skill and skill[field] not in allowed:
            errors.append(f"enum:{field}")
    if "quality_score" in skill:
        q = float(skill["quality_score"])
        if q < 0.0 or q > 1.0:
            errors.append("range:quality_score")
    return (len(errors) == 0, errors)
