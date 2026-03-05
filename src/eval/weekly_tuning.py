from __future__ import annotations

from pathlib import Path
from typing import Dict


def build_weekly_tuning_report(path: Path, metrics: Dict[str, float]) -> None:
    fail_rate = metrics.get("fail_rate", 0.0)
    retry_rate = metrics.get("retry_rate", 0.0)
    p95_latency = metrics.get("p95_latency_ms", 0.0)

    recommendations = []
    if fail_rate > 0.2:
        recommendations.append("Increase policy_fit and quality_score weights by +0.05 each.")
    if retry_rate > 0.3:
        recommendations.append("Reduce batch size and tighten Stage A required_tools filter.")
    if p95_latency > 1200:
        recommendations.append("Increase latency penalty and prefer fast latency_class skills.")
    if not recommendations:
        recommendations.append("Keep current weights; monitor next weekly window.")

    lines = [
        "# Weekly Router Tuning",
        "",
        "## Metrics",
        f"- fail_rate: {fail_rate:.3f}",
        f"- retry_rate: {retry_rate:.3f}",
        f"- p95_latency_ms: {p95_latency:.1f}",
        "",
        "## Recommendations",
    ]
    lines.extend([f"- {r}" for r in recommendations])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
