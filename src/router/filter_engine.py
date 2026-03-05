from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class RouterContext:
    available_tools: List[str]
    approval_token: str | None = None
    allow_deprecated: bool = False


def filter_candidates(skills: List[Dict], ctx: RouterContext) -> Tuple[List[Dict], List[Dict]]:
    passed: List[Dict] = []
    rejected: List[Dict] = []

    for s in skills:
        reason = None
        if s.get("status") != "active" and not ctx.allow_deprecated:
            reason = "status_not_active"
        elif not set(s.get("required_tools", [])).issubset(set(ctx.available_tools)):
            reason = "missing_required_tools"
        elif s.get("risk_level") == "high" and not ctx.approval_token:
            reason = "approval_required"

        if reason:
            rejected.append({"skill_id": s.get("skill_id"), "reason": reason})
        else:
            passed.append(s)

    return passed, rejected
