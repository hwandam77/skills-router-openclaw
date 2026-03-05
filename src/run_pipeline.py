from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from src.registry.inventory import write_inventory
from src.registry.enricher import enrich_skills
from src.registry.schema_validator import validate_skill
from src.router.filter_engine import RouterContext, filter_candidates
from src.router.filter_explain import append_filter_trace
from src.router.shadow_runner import run_shadow_compare, write_shadow_diff_report
from src.router.vector_adapter import KeywordVectorBackend, compute_vector_scores
from src.router.scoring_engine import rank_skills
from src.router.selector import select_for_task
from src.policy.policy_engine import PolicyContext, enforce_policy
from src.eval.golden_runner import GoldenCase, write_golden_report
from src.eval.weekly_tuning import build_weekly_tuning_report


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data = root / "data"
    reports = root / "reports"
    logs = root / "logs" / "router"
    data.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    skills_root = Path("/home/hwandam/.openclaw/workspace/skills")

    # 1) inventory
    inv_path = data / "skill_inventory.json"
    count = write_inventory(skills_root, inv_path)

    # 2) enrich + validate
    skills = json.loads(inv_path.read_text(encoding="utf-8"))
    skills = enrich_skills(skills)

    invalid = []
    for s in skills:
        ok, errs = validate_skill(s)
        if not ok:
            invalid.append({"skill_id": s.get("skill_id"), "errors": errs})

    reg_path = data / "skill_registry_v2.json"
    reg_path.write_text(json.dumps(skills, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 3) Stage A + policy + trace
    run_id = str(uuid4())
    passed, rejected = filter_candidates(skills, RouterContext(available_tools=["read", "exec", "write"]))
    allowed, blocked = enforce_policy(passed, PolicyContext(approval_token=None))
    rejected_all = rejected + blocked
    append_filter_trace(logs / "filter_trace.jsonl", run_id, rejected_all)

    # 4) ranking + select
    docs = {s["skill_id"]: f"{s['skill_id']} {' '.join(s.get('intents', []))} {s.get('domain','')}" for s in allowed}
    vec = compute_vector_scores("debug router policy", docs, backend=KeywordVectorBackend())
    feature_map = {
        s["skill_id"]: {
            "intent_match": 0.8,
            "vector_similarity": vec.get(s["skill_id"], 0.0),
            "quality_score": s.get("quality_score", 0.5),
            "policy_fit": 1.0,
            "latency_fit": 1.0,
            "cost_fit": 1.0,
        }
        for s in allowed
    }
    ranked = rank_skills(allowed, feature_map, has_approval=False)
    selected = select_for_task(ranked, "composite")

    # 5) shadow report
    baseline = [x["skill_id"] for x in ranked[:3]]
    shadow = run_shadow_compare(skills, ["read", "exec", "write"], baseline_selected=baseline)
    write_shadow_diff_report(reports / "shadow_filter_diff.md", shadow)

    # 6) golden eval + weekly tuning reports (seed set)
    golden_cases = [
        GoldenCase("case-1", baseline[0] if baseline else "none", selected[0]["skill_id"] if selected else "none"),
        GoldenCase("case-2", "master-systematic-debugging", (selected[1]["skill_id"] if len(selected) > 1 else "none")),
    ]
    write_golden_report(reports / "golden_eval.md", golden_cases)
    build_weekly_tuning_report(reports / "weekly_router_tuning.md", {
        "fail_rate": 0.18,
        "retry_rate": 0.22,
        "p95_latency_ms": 980,
    })

    summary = {
        "inventory_count": count,
        "invalid_count": len(invalid),
        "allowed_count": len(allowed),
        "rejected_count": len(rejected_all),
        "top_selected": [x["skill_id"] for x in selected],
        "run_id": run_id,
    }
    (reports / "pipeline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
