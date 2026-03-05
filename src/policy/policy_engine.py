from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class PolicyContext:
    approval_token: str | None = None


def evaluate_policy(skill: Dict, ctx: PolicyContext) -> Tuple[bool, str | None]:
    risk = skill.get("risk_level", "low")
    if risk == "high" and not ctx.approval_token:
        return False, "policy_block:approval_required"

    dangerous = set(skill.get("dangerous_actions", []))
    if dangerous and not ctx.approval_token:
        return False, "policy_block:dangerous_action_requires_approval"

    return True, None


def enforce_policy(skills: List[Dict], ctx: PolicyContext) -> Tuple[List[Dict], List[Dict]]:
    allowed, blocked = [], []
    for s in skills:
        ok, reason = evaluate_policy(s, ctx)
        if ok:
            allowed.append(s)
        else:
            blocked.append({"skill_id": s.get("skill_id"), "reason": reason})
    return allowed, blocked
