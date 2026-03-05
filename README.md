# skills-router-openclaw

Scalable skill routing prototype for OpenClaw environments with 100~400+ skills.

## What this project does

- Builds a local skill registry from installed `SKILL.md` files
- Applies **Stage A filter** (status/tools/risk/policy)
- Applies **Stage B ranking** (intent + semantic fallback + quality + policy fit)
- Selects Top-K skills for simple/composite tasks
- Persists run results in SQLite
- Exposes a lightweight FastAPI interface for planning/execution

## Architecture (v1)

- `src/registry/` — inventory, schema validation, enrichment
- `src/router/` — filtering, scoring, vector adapter, selection, shadow compare
- `src/policy/` — policy enforcement, approval flow, safety reports
- `src/obs/` — trace logging
- `src/eval/` — golden evaluation, weekly tuning reports
- `src/api/` — runtime API layer
- `src/storage/` — run store (SQLite)

## API

- `GET /router/health`
- `POST /router/reload`
- `POST /router/plan`
- `POST /router/execute`
- `GET /router/runs/{run_id}`

## Quick start

```bash
cd /home/hwandam/project/skill-router-v1
python3 -m pytest -q
./scripts/run_api.sh
```

Open another terminal:

```bash
curl http://127.0.0.1:8091/router/health
curl -X POST http://127.0.0.1:8091/router/plan \
  -H 'Content-Type: application/json' \
  -d '{
    "user_intent":"debug api timeout",
    "available_tools":["read","exec"],
    "task_type":"simple"
  }'
```

## Pipeline artifacts

Running the pipeline:

```bash
PYTHONPATH=. python3 -m src.run_pipeline
```

Generates:
- `data/skill_inventory.json`
- `data/skill_registry_v2.json`
- `reports/shadow_filter_diff.md`
- `reports/golden_eval.md`
- `reports/weekly_router_tuning.md`
- `reports/pipeline_summary.json`
- `logs/router/filter_trace.jsonl`

## Current status

- Implementation baseline complete (v1 skeleton)
- Tests passing
- Ready for production integration tasks:
  - real vector backend
  - production registry source
  - service hardening and auth

## Docs

See `docs/` for planning/spec documents:
- `SKILL_ROUTER_V1_PLAN.md`
- `SKILL_REGISTRY_SCHEMA.md`
- `ROUTING_POLICY.md`
- `ROUTER_API_SPEC.md`
- `SCORING_SPEC.md`
- `POLICY_SAFETY_SPEC.md`
- `PHASE_ROADMAP.md`
- `IMPLEMENTATION_TASKS.md`
- `IMPLEMENTATION_STATUS_2026-03-05.md`
