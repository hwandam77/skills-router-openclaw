from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class GoldenCase:
    task_id: str
    expected_skill: str
    predicted_skill: str


def evaluate_precision(cases: List[GoldenCase]) -> float:
    if not cases:
        return 0.0
    hit = sum(1 for c in cases if c.expected_skill == c.predicted_skill)
    return hit / len(cases)


def write_golden_report(path: Path, cases: List[GoldenCase]) -> None:
    precision = evaluate_precision(cases)
    lines = [
        "# Golden Eval Report",
        "",
        f"- Cases: {len(cases)}",
        f"- Precision@1: {precision:.3f}",
        "",
        "## Cases",
    ]
    for c in cases:
        ok = "✅" if c.expected_skill == c.predicted_skill else "❌"
        lines.append(f"- {ok} {c.task_id}: expected={c.expected_skill}, predicted={c.predicted_skill}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
