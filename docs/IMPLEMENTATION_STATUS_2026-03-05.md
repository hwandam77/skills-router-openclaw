# Implementation Status (2026-03-05)

## Completed
- T0-1 inventory collector (`src/registry/inventory.py`)
- T0-2 schema validator (`src/registry/schema_validator.py`)
- T0-3 enricher (`src/registry/enricher.py`)
- T1-1 Stage A filter (`src/router/filter_engine.py`)
- T1-2 filter explain log (`src/router/filter_explain.py`)
- T1-3 shadow runner + report (`src/router/shadow_runner.py`)
- T2-1 scoring engine (`src/router/scoring_engine.py`)
- T2-2 vector adapter + fallback (`src/router/vector_adapter.py`)
- T2-3 selector (`src/router/selector.py`)
- T3-1 policy engine (`src/policy/policy_engine.py`)
- T3-2 approval flow (`src/policy/approval.py`)
- T3-3 safety report writer (`src/policy/safety_report.py`)
- T4-1 trace logger (`src/obs/trace.py`)
- T4-2 golden eval runner (`src/eval/golden_runner.py`)
- T4-3 weekly tuning report (`src/eval/weekly_tuning.py`)
- TAPI-1 types (`src/router/types.py`)
- TAPI-2 endpoints (`src/api/app.py`)
- TAPI-3 contract/openapi tests (`tests/api/*`)
- End-to-end pipeline runner (`src/run_pipeline.py`)

## Generated artifacts
- `data/skill_inventory.json`
- `data/skill_registry_v2.json`
- `reports/shadow_filter_diff.md`
- `reports/golden_eval.md`
- `reports/weekly_router_tuning.md`
- `reports/pipeline_summary.json`
- `logs/router/filter_trace.jsonl`

## Test result
- `python3 -m pytest -q`
- Passed: 23

## Notes
- This is v1 implementation baseline/skeleton with deterministic local behavior.
- Next recommended step: wire real vector provider + production registry source + persistent run store.
