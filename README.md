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
cd /home/hwandam/project/skills-router-openclaw
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

## Expected Impact in OpenClaw (적용 기대 효과)

### 1) 스킬 선택 비용 절감 (핵심)
- 기존: 400+ 스킬 설명을 광범위하게 읽고 선택 → 요청당 토큰 소비 급증
- 적용 후: `Stage A 필터(400 -> 10~20)` -> `Stage B 랭킹` -> Top-K 선택
- 기대 절감: **요청당 토큰 약 90~95% 절감**

### 2) 선택 품질 안정화
- 유사 스킬 혼동: `conflicts` 기반 사전 차단
- deprecated 스킬: 패널티로 자동 하위 랭킹
- 도구 없는 스킬: Stage A에서 선제 제거
- 모호한 의도: composite 경로 Top-K 복수 후보 반환

### 3) 보안/정책 일관성
- high-risk + 승인토큰 없음 => 정책 엔진에서 자동 차단
- 외부전송/파괴적 작업은 승인 플로우 전제

### 4) 400+ 스킬 확장 대응
- 라우팅 비용 구조: Stage A `O(n)` + Stage B `O(k log k)`
- 실제 LLM 컨텍스트 크기는 후보군(10~20개) 중심으로 고정

### 5) 운영 가시성(Observability)
- `logs/router/filter_trace.jsonl` — 탈락 사유 추적
- `reports/golden_eval.md` — 선택 정확도 측정
- SQLite RunStore — 실행 기록 보존
- Shadow mode 리포트 — 회귀 감지

### 6) 주간 자동 튜닝 기반
- Golden task 기준 품질 점검
- fail/retry/latency 지표 기반 가중치 조정 루프

### 종합 임팩트 요약

| 지표 | 현재(일반) | Router 적용 후 |
|---|---|---|
| 요청당 토큰 | 스킬 전체 참조 시 높음 | 후보 10~20개 중심으로 축소 |
| 선택 정확도 | 편차 큼 | SLO 기반 개선(목표 ≥ 85%) |
| 위험 스킬 오선택 | LLM 의존 | 정책 엔진 강제 차단 |
| 400+ 스킬 확장 | 비용/복잡도 증가 | 구조적 대응 가능 |
| 선택 이유 추적 | 제한적 | 로그/리포트로 추적 가능 |

> Note: current v1 uses deterministic local semantic fallback. Connecting a stronger embedding backend can improve intent matching further.

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
