from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ScoringWeights:
    intent_match: float = 0.35
    vector_similarity: float = 0.25
    quality_score: float = 0.15
    policy_fit: float = 0.10
    latency_fit: float = 0.08
    cost_fit: float = 0.07


@dataclass
class ScoringPenalties:
    conflict_penalty: float = 0.30
    deprecated_penalty: float = 0.50
    high_risk_no_approval: float = 0.80


def score_skill(skill: Dict, features: Dict[str, float], has_approval: bool = False,
                penalties: ScoringPenalties | None = None,
                weights: ScoringWeights | None = None) -> float:
    penalties = penalties or ScoringPenalties()
    weights = weights or ScoringWeights()

    s = (
        weights.intent_match * float(features.get("intent_match", 0.0))
        + weights.vector_similarity * float(features.get("vector_similarity", 0.0))
        + weights.quality_score * float(features.get("quality_score", skill.get("quality_score", 0.0)))
        + weights.policy_fit * float(features.get("policy_fit", 1.0))
        + weights.latency_fit * float(features.get("latency_fit", 1.0))
        + weights.cost_fit * float(features.get("cost_fit", 1.0))
    )

    if skill.get("status") == "deprecated":
        s -= penalties.deprecated_penalty
    if skill.get("risk_level") == "high" and not has_approval:
        s -= penalties.high_risk_no_approval
    if features.get("has_conflict", 0):
        s -= penalties.conflict_penalty

    return round(s, 6)


def rank_skills(skills: List[Dict], feature_map: Dict[str, Dict[str, float]], has_approval: bool = False) -> List[Dict]:
    ranked = []
    for skill in skills:
        sid = skill.get("skill_id")
        f = feature_map.get(sid, {})
        score = score_skill(skill, f, has_approval=has_approval)
        ranked.append({"skill_id": sid, "score": score})
    return sorted(ranked, key=lambda x: x["score"], reverse=True)
