# Skill Router v1 Plan

작성일: 2026-03-05
최종 업데이트: 2026-03-05 (OpenClaw 벤치마킹 반영)
목표: OpenClaw 스킬 수가 100~400+ 로 증가하고 서브에이전트/오케스트레이션이 확장되는 상황에서, 안정적·설명가능·확장 가능한 라우팅 체계를 구축한다.

---

## 1) Problem Statement

현재 방식 (설명 기반 선택 + 부분적 수동 선별) 은 스킬 수가 많아질수록 다음 문제가 발생한다.

1. 선택 비용 증가
- 매 요청마다 후보가 과도하게 많아짐
- 잘못된 스킬 선택 확률 증가

2. 품질 불안정
- 요청 표현 차이에 따라 선택 편차 발생
- 유사 스킬 간 충돌/중복 선택

3. 오케스트레이션 복잡도 폭증
- 서브에이전트가 늘수록 실행경로 추적 어려움
- 실패 원인 분석 (선택 실패 vs 실행 실패) 분리 곤란

4. 운영 리스크
- 고위험 스킬 (외부 전송/파괴적 명령) 제어 취약
- 비용/지연/재시도 정책 비일관

5. **의존성 관리 부재** (새로 추가)
- 스킬 실행 전 도구 설치 상태 확인 없음
- 수동 설치 과정으로 사용자 경험 저하
- "도구 없음" 실패와 "스킬 실행" 실패 구분 불가

---

## 2) Design Goals

1. Scale
- 400+ 스킬에서도 평균 선택 지연 일정 수준 유지

2. Reliability
- 동일 의도 입력 시 일관된 상위 후보 반환

3. Explainability
- 왜 해당 스킬을 선택/배제했는지 로그로 설명 가능

4. Safety
- 정책 엔진으로 위험 스킬/행동을 중앙 통제

5. Operability
- 지표 기반 (정확도/실패율/지연/비용) 개선 루프 구축

6. **Automation** (새로 추가)
- 스킬 의존성 자동 설치 및 상태 검증
- 설치 실패 시 자동 피드백 및 대체 스킬 제안

7. **Adaptability** (새로 추가)
- 실시간 실패율/지연 시간 기반 동적 점수 조정
- 컨텍스트 (채널/세션) 에 따른 자동 스킬 필터링

---

## 3) High-Level Architecture

### 3.1 Two-Stage Routing

1) Stage A: Fast Candidate Filter
- 메타데이터 규칙 필터로 400 -> 10~20 개 축소
- 기준: domain/intents/risk/required-tools/conflicts/status(deprecated)
- **추가: 의존성 검증 (installChecks)**

2) Stage B: Rank & Select
- 벡터 유사도 + 규칙 점수 + 실행정책 점수 결합
- **추가: 실시간 Health Metrics 반영**
- 최종 Top-K(1~3) 선택

### 3.2 Split Control Planes

- Planner Plane
  - 요청 의도 해석, 후보 선택, 실행 계획 생성
- Executor Plane
  - 실제 실행, retry/timeout, circuit-breaker, rollback
- Policy Plane
  - allow/deny, 위험 행동 차단, 승인 게이트
- **Dependency Plane** (새로 추가)
  - 스킬 의존성 설치/검증 자동화
  - 환경 상태 체크 및 대체 방안 제안

### 3.3 Observability Plane

각 실행에 대해 아래를 기록:
- run_id, trace_id
- shortlisted_skills, selected_skills, rejected_reason
- stage_latency_ms
- fail_class (context_miss/tool_fail/validation_fail/timeout/policy_block/dependency_fail)
- outcome (success/fail/partial)
- **추가: health_metrics_snapshot** (실행 당시 스킬 상태)

### 3.4 Golden Task Eval Framework (새로 추가)

- 일일/주간 Golden Task 자동 실행
- 라우팅 정확도 (Precision/Recall) 추적
- 회귀 테스트 자동화
- **설치: `tests/golden-tasks/` 디렉토리**

---

## 4) Skill Registry Schema (v2)

각 스킬은 최소 메타 필드를 가져야 함.

### 필수 필드
- skill_id
- version (semver)
- domain (backend/devops/frontend/security/ops/...)
- intents[]
- risk_level (low/medium/high)
- required_tools[]
- latency_class (fast/normal/slow)
- cost_class (low/normal/high)
- conflicts[]
- dependencies[]
- status (active/deprecated/experimental)
- quality_score (offline eval 기반)

### **새로 추가: Installation & Dependency**
- install[] (OpenClaw 방식 벤치마킹)
  - id, kind (brew/apt/npm/pip/dnf/...), formula/package, bins[], label, required
- environment_checks[]
  - command, error_message, fallback_suggestion
- install_policy (auto/confirm/deny)

### **새로 추가: Runtime Metrics** (실시간 업데이트)
- metrics (동적 필드)
  - success_rate_7d, avg_latency_ms, error_rate_7d
  - last_failure_at, failure_class
  - usage_count_7d

### **새로 추가: Versioning & Compatibility**
- compatibility
  - min_router_version, deprecated_in, replaced_by
- changelog[] (version, date, changes[])

### **새로 추가: Context Awareness**
- available_in[] (channels: slack/discord/whatsapp/local...)
- group_policy (allow/deny/require_mention)
- permissions_required[]

### **새로 추가: Model Fit**
- model_strengths[] (code/debug/creative/analytics...)
- preferred_models[] (모델 ID 목록)

이 메타는 라우팅의 1 차 필터와 정책 엔진의 입력이 된다.

---

## 5) Scoring Model (v2)

최종 점수 =

`S = w1*intent_match + w2*vector_similarity + w3*quality_score + w4*policy_fit + w5*latency_fit + w6*cost_fit + w7*model_fit - penalties`

### **새로 추가: Health Penalty**
- recent_failure_penalty = (실패율_7 일) × 0.3
- latency_degradation_penalty = (현재 지연 - 기준 지연) / 기준 지연
- availability_penalty = (현재 사용 불가능) ? 1.0 : 0

### **새로 추가: Context Bonus**
- channel_fit_bonus = (현재 채널과 일치) ? 0.1 : 0
- permission_bonus = (권한 충족) ? 0.05 : -0.2

### **새로 추가: Installation Readiness**
- install_ready_bonus = (의존성 충족) ? 0.1 : -0.5
- install_confirmed_bonus = (설치 확인됨) ? 0.05 : 0

- penalties 예시:
  - conflict_penalty
  - deprecated_penalty
  - high_risk_without_approval_penalty
  - environment_mismatch_penalty

기본 Top-K:
- 단일 작업: Top-1
- 복합 작업: Top-2~3 (planner 분해 시)

---

## 6) Policy & Safety

### 6.1 Mandatory Rules

- high risk 스킬은 human approval token 없으면 실행 금지
- destructive/external-send 계열은 정책 엔진 단일 진입
- deprecated 스킬은 기본 배제 (명시 override 필요)

### 6.2 **Enhanced Approval Flow** (보강)

- approvalPolicy: 'auto' | 'require_approval' | 'deny'
- pendingApprovals: 실시간 승인 요청 대기 목록
- approval_timeout: 승인 요청 유효 기간 (기본 30 분)
- approval_history: 승인/거부 이력 감사 로그

### 6.3 Multi-Agent Safety

- 서브에이전트별 tool allowlist 분리
- run budget (max_steps/max_time/max_cost) 강제
- 동일 실패 2 회 시 전략 변경 또는 실행 중단
- **추가: 실패 시 자동 대체 스킬 제안**

### 6.4 **Channel-Level Restrictions** (새로 추가)

- Slack 그룹 채널: `system.run` 등 위험 스킬 자동 배제
- Discord 봇: 채널 권한 기반 스킬 제한
- WhatsApp 개인 채널: 전체 스킬 허용

---

## 7) Rollout Plan

### Phase 0 (1 주) — Inventory & Metadata Enhancement
- 기존 스킬 전수 스캔
- Skill Registry 메타 템플릿 강제 (install 필드 포함)
- 충돌/중복/deprecated 후보 목록화
- **추가: Golden Task 30 개 정의 및 테스트 프레임워크 구축**

### Phase 1 (1~2 주) — Filter Router + Dependency Check
- Stage A 필터 구현
- **의존성 설치/검증 로직 추가**
- 기존 수동 라우팅과 병행 (A/B 비교)
- **Shadow 모드 구현**

### Phase 2 (1~2 주) — Rank Router + Health Metrics
- Stage B 점수식 도입
- **실시간 Health Metrics 연동**
- Top-K 선택 + 선택 근거 로그
- **Model Fit 보정 로직 추가**

### Phase 3 (1 주) — Policy & Guardrails
- 위험 스킬 승인 게이트
- **승인 워크플로우 대시보드**
- 정책 차단 이벤트 대시보드화
- **Channel-level 정책 구현**

### Phase 4 (지속) — Eval/Feedback Loop
- **Golden Task 기반 주간 정확도 리포트**
- 실패분류 기반 주간 재학습 (가중치/정책 튜닝)
- **Health Metrics 기반 동적 점수 조정**
- **Install success rate 모니터링**

### **Phase 5 (추가) — Advanced Features** (2~3 주)
- **컨텍스트 aware 스킬 프루닝**
- **버전 관리 및 롤백 전략 구현**
- **Multi-model fallback 오케스트레이션**
- **사용자 선호도 기반 커스터마이징**

---

## 8) Success Metrics (SLO)

### 라우팅 성능
- P50 routing latency < 300ms
- P95 routing latency < 1200ms
- **Dependency check latency < 100ms**

### 정확도
- Top-1 selection precision >= 85% (golden tasks)
- **Top-3 recall >= 90% (golden tasks)**
- **Shadow mode agreement rate >= 80%**

### 안전성
- policy violation leakage = 0
- **Dependency failure rate < 1%**

### 복구
- reroute-after-failure recovery rate >= 70%
- **Auto-substitution success rate >= 60%**

### **사용자 경험 (신규)**
- **Install success rate >= 95%**
- **Manual install requests < 5%**
- **Average time-to-first-success <= 30 sec**

---

## 9) Deliverables

1. `docs/SKILL_ROUTER_V1_PLAN.md` (본 문서)
2. `docs/SKILL_REGISTRY_SCHEMA.md` (v2 확장)
3. `docs/ROUTING_POLICY.md`
4. `docs/PHASE_ROADMAP.md`
5. `docs/INSTALLATION_GUIDE.md` (신규 - 의존성 자동화 가이드)
6. `docs/GOLDEN_TASKS.md` (신규 - 평가 체계)
7. `src/router/` (필터/랭커 스켈레톤)
8. `src/dependency/` (신규 - 의존성 관리)
9. `tests/golden-tasks/` (신규 - 평가 데이터셋)
10. `tests/router/` (golden task 기반 기본 테스트)
11. `eval/` (신규 - 자동 평가 스크립트)

---

## 10) Immediate Next Actions

1. 현재 설치된 스킬 목록 + 메타 필드 추출
2. 누락 메타 자동 보정 규칙 작성
3. golden routing task 30 개 정의
4. Stage A 필터 프로토타입 구현
5. **Install metadata 템플릿 작성 및 스켈레톤 생성**
6. **Golden Task Test Framework 설계**
7. **Health Metrics 수집 스키마 정의**

---

## 11) OpenClaw 벤치마킹 핵심 교훈

### 11.1 What Works Well in OpenClaw
- **Installation Automation**: `install[]` 메타데이터로 의존성 자동 설치
- **Environment Validation**: 실행 전 도구 상태 체크
- **Channel-Level Control**: 채널별로 다른 정책 적용
- **Clear Documentation**: `SKILL.md` 의 인간 가독성 우선 설계

### 11.2 What We Improve Upon
- **Structured Metrics**: JSON 기반 메타데이터로 자동화 용이
- **Dynamic Scoring**: 실시간 Health Metrics 반영
- **Shadow Mode**: 변경 사항 회귀 방지
- **Golden Tasks**: 정량적 평가 체계
- **Context Awareness**: 채널/세션별 적응형 라우팅

### 11.3 Hybrid Approach
- **OpenClaw 스타일**: `SKILL.md` 에 인간 가독성 높은 설명 포함
- **v1 스타일**: JSON 메타데이터로 자동화/라우팅 최적화
- **결과**: 인간 친화성 + 머신 친화성 동시 확보

---

## Appendix A: Why this is better than pure vector search

- pure vector 는 표현 유사도에는 강하지만, 정책/위험/도구제약을 설명하지 못함
- 본 설계는 벡터를 2 차 랭킹 요소로 사용하고, 1 차는 운영 제약 기반으로 안전하게 축소
- **의존성 자동화로 실패 원인 분리 명확화**
- **실시간 메트릭으로 동적 최적화 가능**
- 결과적으로 안정성/설명가능성/확장성이 동시 개선됨

---

## Appendix B: Risk & Mitigation

| 위험 | 영향도 | 발생 가능성 | 완화 방안 |
|------|--------|-------------|-----------|
| 의존성 자동 설치 실패 | 높음 | 중 | 수동 설치 가이드 자동 생성, 대체 스킬 제안 |
| Health Metrics 수집 오버헤드 | 중 | 높음 | 샘플링 전략, 비동기 수집 |
| Golden Task 편향 | 중 | 중 | 주기적 Task 갱신, 다중 시나리오 |
| Approval 워크플로우 지연 | 높음 | 중 | 타임아웃 자동 거절, 우선순위 큐 |
| Channel 정책 오버스펙트 | 낮음 | 낮음 | 초기에는 whitelist 기반, 점진적 확장 |

---

## Appendix C: Glossary

- **Golden Task**: 라우팅 정확도 평가를 위한 예상 결과가 있는 테스트 작업
- **Shadow Mode**: 새 라우터가 기존 라우터와 병행 실행되어 결과 비교하는 모드
- **Health Metrics**: 실패율, 지연 시간, 사용량 등 실시간 스킬 상태 지표
- **Install Policy**: 의존성 자동 설치 허용 정책 (auto/confirm/deny)
- **Context-Aware**: 채널/세션/권한에 따라 동적 스킬 필터링