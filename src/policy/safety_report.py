from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import List, Dict


def write_safety_report(path: Path, blocked_events: List[Dict]) -> None:
    c = Counter(evt.get("reason", "unknown") for evt in blocked_events)
    lines = [
        "# Policy Safety Weekly Report",
        "",
        f"- total_blocked: {len(blocked_events)}",
        "",
        "## Breakdown",
    ]
    for reason, n in c.most_common():
        lines.append(f"- {reason}: {n}")

    lines.append("\n## Raw Events")
    for e in blocked_events[:50]:
        lines.append(f"- skill={e.get('skill_id')} reason={e.get('reason')}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
