# IMPLEMENTATION_TASKS.md

작성일: 2026-03-05
기준 문서:
- `SKILL_ROUTER_V1_PLAN.md`
- `ROUTER_API_SPEC.md`
- `REGISTRY_SPEC.md`
- `SCORING_SPEC.md`
- `ROUTING_POLICY.md`
- `POLICY_SAFETY_SPEC.md`
- `PHASE_ROADMAP.md`

---

## 0) 구현 원칙

- 작은 배치(1~3 파일, 50~200 LOC)로 진행
- 단계별 완료 증거(테스트/로그/샘플 출력) 필수
- Mandatory 정책 위반 시 merge 금지

---

## 1) Phase 0 — Inventory & Registry Baseline

### T0-1. 스킬 인벤토리 수집기 구현
- 산출물: `src/registry/inventory.py`
- 내용:
  - `skills/**/SKILL.md` 스캔
  - 기본 메타(skill_id, version, status, domain, intents…) 추출
- 완료 조건:
  - JSON 출력: `data/skill_inventory.json`

### T0-2. Registry 스키마 validator 구현
- 산출물: `src/registry/schema_validator.py`
- 내용:
  - Required 필드 검증
  - enum/range/type 검증
- 완료 조건:
  - `tests/registry/test_schema_validator.py` 통과

### T0-3. 누락 메타 자동 보정기
- 산출물: `src/registry/enricher.py`
- 내용:
  - 누락 `latency_class/cost_class/risk_level` 기본값 채움
  - deprecated/conflict 후보 자동 플래그
- 완료 조건:
  - `data/skill_registry_v2.json` 생성

---

## 2) Phase 1 — Stage A Filter Router

### T1-1. Filter 엔진 구현
- 산출물: `src/router/filter_engine.py`
- 규칙:
  - status active
  - required_tools 충족
  - risk approval 체크
  - conflicts/dependencies 체크
- 완료 조건:
  - 후보 수 축소 로그 출력(예: 300→18)

### T1-2. Filter 결과 설명 로그
- 산출물: `src/router/filter_explain.py`
- 내용:
  - reject 이유 코드(`missing_tool`, `risk_block`, `deprecated`)
- 완료 조건:
  - `logs/router/filter_trace.jsonl` 생성

### T1-3. Shadow 모드 연결
- 산출물: `src/router/shadow_runner.py`
- 내용:
  - 기존 라우팅 vs 새 필터 결과 병행 기록
- 완료 조건:
  - 비교 리포트 `reports/shadow_filter_diff.md`

---

## 3) Phase 2 — Stage B Ranking

### T2-1. Scoring 엔진 구현
- 산출물: `src/router/scoring_engine.py`
- 내용:
  - `S = w1..w6 - penalties` 공식 구현
  - 가중치/페널티는 config로 분리
- 완료 조건:
  - deterministic 점수 재현 테스트 통과

### T2-2. Vector similarity 어댑터
- 산출물: `src/router/vector_adapter.py`
- 내용:
  - memory/vector backend 연동 추상화
  - 실패 시 fallback(semantic=0, rule-only)
- 완료 조건:
  - 벡터 비활성 환경에서도 라우터 동작

### T2-3. Top-K 선택기
- 산출물: `src/router/selector.py`
- 내용:
  - 단일 작업 Top-1
  - 복합 작업 Top-2~3
- 완료 조건:
  - `tests/router/test_topk_selection.py` 통과

---

## 4) Phase 3 — Policy & Safety Enforcement

### T3-1. Policy 엔진
- 산출물: `src/policy/policy_engine.py`
- 내용:
  - high-risk 승인 토큰 확인
  - destructive/external-send 게이트
- 완료 조건:
  - 정책 차단 이벤트 로그 남김

### T3-2. Approval flow 구현
- 산출물: `src/policy/approval.py`
- 내용:
  - 승인 토큰 검증/만료/재사용 방지
- 완료 조건:
  - `tests/policy/test_approval_flow.py` 통과

### T3-3. Safety report 생성기
- 산출물: `src/policy/safety_report.py`
- 내용:
  - 차단 사유/빈도/스킬별 위험 리포트
- 완료 조건:
  - `reports/policy_safety_weekly.md`

---

## 5) Phase 4 — Observability & Eval Loop

### T4-1. 실행 추적 표준화
- 산출물: `src/obs/trace.py`
- 내용:
  - run_id/trace_id/stage_latency/fail_class 표준 로그
- 완료 조건:
  - JSONL 로그 스키마 검증 통과

### T4-2. Golden Task 평가 러너
- 산출물: `src/eval/golden_runner.py`
- 내용:
  - Golden tasks 30개 기준 precision/recall 측정
- 완료 조건:
  - `reports/golden_eval.md` 생성

### T4-3. 주간 튜닝 루프
- 산출물: `src/eval/weekly_tuning.py`
- 내용:
  - 실패분류 기반 가중치 튜닝 제안
- 완료 조건:
  - `reports/weekly_router_tuning.md`

---

## 6) API 구현 태스크 (ROUTER_API_SPEC 기준)

### TAPI-1. 타입/DTO 구현
- `src/router/types.ts` (또는 Python dataclass/pydantic)

### TAPI-2. 엔드포인트 구현
- `POST /router/plan`
- `POST /router/execute`
- `GET /router/runs/{run_id}`
- `GET /router/health`

### TAPI-3. 계약 테스트
- `tests/api/test_router_contract.py`
- OpenAPI/JSON schema 스냅샷 테스트

---

## 7) 필수 테스트 매트릭스

- Unit
  - filter/scoring/policy 개별 로직
- Integration
  - registry + router + policy end-to-end (local only)
- E2E
  - 샘플 요청 10개에 대해 선택/실행/로그 확인
- Non-functional
  - latency/cost budget 검증
  - failover(벡터 unavailable) 검증

---

## 8) 우선순위 Backlog (실행 순서)

P0 (이번 주)
1. T0-1, T0-2, T1-1, T1-2
2. T2-1 (rule-only scoring)
3. T3-1 (기본 policy block)

P1 (다음 주)
4. T2-2, T2-3, T4-1
5. TAPI-1, TAPI-2

P2
6. T4-2, T4-3, TAPI-3
7. Safety/weekly reports 자동화

---

## 9) 완료 정의 (Definition of Done)

각 태스크는 아래 충족 시 완료:
- 코드 + 문서 동시 갱신
- 테스트 통과 로그 첨부
- run_id 기반 실행 증거(JSONL) 첨부
- 변경 요약 3줄(what/why/verification)

---

## 10) 즉시 실행 명령 (bootstrap)

```bash
cd /home/hwandam/project/skill-router-v1
mkdir -p data logs reports src/{registry,router,policy,obs,eval} tests/{registry,router,policy,api}
```

