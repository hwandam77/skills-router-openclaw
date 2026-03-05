from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from src.router.filter_engine import RouterContext, filter_candidates


def run_shadow_compare(skills: List[Dict], available_tools: List[str], baseline_selected: List[str]) -> Dict:
    filtered, rejected = filter_candidates(skills, RouterContext(available_tools=available_tools))
    shadow_selected = [s["skill_id"] for s in filtered][:3]

    baseline_set = set(baseline_selected)
    shadow_set = set(shadow_selected)

    return {
        "baseline_selected": baseline_selected,
        "shadow_selected": shadow_selected,
        "added": sorted(shadow_set - baseline_set),
        "removed": sorted(baseline_set - shadow_set),
        "rejected_count": len(rejected),
    }


def write_shadow_diff_report(path: Path, result: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# Shadow Filter Diff Report",
        "",
        f"- Baseline: {', '.join(result['baseline_selected']) or '(none)'}",
        f"- Shadow: {', '.join(result['shadow_selected']) or '(none)'}",
        f"- Added: {', '.join(result['added']) or '(none)'}",
        f"- Removed: {', '.join(result['removed']) or '(none)'}",
        f"- Rejected count: {result['rejected_count']}",
    ]
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
