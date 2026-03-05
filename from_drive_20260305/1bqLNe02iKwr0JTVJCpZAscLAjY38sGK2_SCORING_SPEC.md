# Scoring Model 상세 Spec (v1)

작성일: 2026-03-05

---

## 1. 최종 점수 공식

```
S = w1*intentMatch + w2*vectorSimilarity + w3*qualityScore
    + w4*policyFit + w5*latencyFit + w6*costFit
    - sum(penalties)
```

### 1.1 초기 가중치 (v1 기본값)

| 컴포넌트 | 변수 | 초기 가중치 | 근거 |
|---------|------|-----------|------|
| Intent Match | w1 | **0.35** | 가장 직접적인 선택 신호 |
| Vector Similarity | w2 | **0.25** | 의미 유사도 (표현 변형 대응) |
| Quality Score | w3 | **0.15** | 오프라인 평가 기반 품질 |
| Policy Fit | w4 | **0.10** | 위험도/예산 적합성 |
| Latency Fit | w5 | **0.08** | 응답속도 제약 충족도 |
| Cost Fit | w6 | **0.07** | 비용 제약 충족도 |
| **합계** | | **1.00** | |

### 1.2 페널티 값

| 페널티 | 값 | 발동 조건 |
|-------|-----|---------|
| conflict_penalty | -0.30 | 선택 스킬 간 conflicts[] 교차 |
| deprecated_penalty | -0.50 | status = deprecated |
| high_risk_no_approval | -0.80 | risk_level=high + approvalToken 없음 |
| budget_exceeded | -0.20 | latency/cost class 초과 |

---

## 2. Intent Match (w1)

### 2.1 Intent 추출 파이프라인

```
userIntent (자연어)
    │
    ▼
[1] 전처리: 소문자화, 불용어 제거
    │
    ▼
[2] 키워드 추출: TF-IDF + 도메인 사전 기반
    │  예: "파이썬 타입 에러 디버깅" → ["debug", "error", "python", "type"]
    ▼
[3] Intent 매핑: 키워드 → 표준 intent 레이블
    │  도메인 사전: debug→debug, 디버깅→debug, 에러→error, fix→fix-error
    ▼
[4] ParsedIntent { labels: string[], isComposite: bool, isAmbiguous: bool }
```

### 2.2 매칭 점수 계산

**Jaccard Similarity** (기본)

```typescript
function intentMatchScore(
  userIntents: string[],
  skillIntents: string[]
): number {
  const intersection = userIntents.filter(i => skillIntents.includes(i));
  const union = new Set([...userIntents, ...skillIntents]);
  return intersection.length / union.size;
}
```

**Fuzzy Bonus**: 완전 일치가 아닌 부분 매칭(edit distance ≤ 2)은 0.5 가중치로 계산.

### 2.3 도메인 사전 (초기 버전)

```yaml
# .omc/registry/intent-dict.yml
aliases:
  # 디버깅
  debug: [디버깅, debug, 에러수정, fix, 오류, troubleshoot]
  root-cause-analysis: [근본원인, rca, 원인분석]

  # 코드 품질
  code-review: [코드리뷰, review, 리뷰, 검토]
  refactor: [리팩토링, refactor, 개선, cleanup]

  # 계획
  plan: [기획, 계획, 설계, planning, design]
  brainstorm: [브레인스토밍, ideation, 아이디어]

  # 검색
  search: [찾기, find, 검색, lookup]

  # 보안
  security: [보안, security, vulnerability, 취약점]

  # 테스트
  tdd: [tdd, 테스트, test, 테스트주도]
```

---

## 3. Vector Similarity (w2)

### 3.1 임베딩 전략

**임베딩 대상**: `skill.description + " " + skill.intents.join(" ")`

**모델 선택**:

| 옵션 | 모델 | 장점 | 단점 |
|------|-----|------|------|
| **A (권장)** | Claude API `text-embedding` | 정확도 높음 | API 비용 발생 |
| B | `all-MiniLM-L6-v2` (로컬) | 무료, 빠름 | 한국어 약함 |
| C | In-memory TF-IDF | 설치 불필요 | 의미 파악 제한 |

**Phase 0~1**: 옵션 C (TF-IDF) 로 시작 → Phase 2부터 옵션 A 전환.

### 3.2 벡터 저장

```
.omc/registry/embeddings/
├── skills.vectors    # float32[], shape: [N_skills, dim]
├── skills.ids        # skill_id 순서 배열 (JSON)
└── metadata.json     # { model, dim, created_at }
```

**유사도 계산**: Cosine Similarity

```typescript
function cosineSimilarity(a: Float32Array, b: Float32Array): number {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] ** 2;
    normB += b[i] ** 2;
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}
```

**Stage B에서만 사용** (Stage A는 메타데이터 필터만).

### 3.3 쿼리 임베딩 캐시

동일 쿼리의 반복 임베딩을 방지:

```typescript
const queryCache = new LRUCache<string, Float32Array>({ max: 100 });
```

---

## 4. Quality Score (w3)

### 4.1 점수 구성 (오프라인 평가)

```
quality_score = 0.4 * precision_score    // golden tasks 정확도
              + 0.3 * reliability_score  // 동일 입력 일관성
              + 0.3 * freshness_score    // last_verified_at 최신성
```

### 4.2 freshness_score 계산

```typescript
function freshnessScore(lastVerifiedAt: string): number {
  const daysSince = daysDiff(new Date(lastVerifiedAt), new Date());
  if (daysSince <= 7)   return 1.0;
  if (daysSince <= 30)  return 0.8;
  if (daysSince <= 90)  return 0.6;
  return 0.4;
}
```

### 4.3 초기값

메타에 `quality_score` 없는 스킬의 초기값:

- `status: active` → 0.60
- `status: experimental` → 0.40
- `status: deprecated` → 0.10

---

## 5. Policy Fit (w4)

```typescript
function policyFitScore(skill: SkillMeta, ctx: RouterContext): number {
  let score = 1.0;

  // risk 패널티는 별도 penalty로 처리됨. 여기선 예산 적합성만.
  if (ctx.budgetConstraints?.latencyClass) {
    const allowed = LATENCY_ORDER[ctx.budgetConstraints.latencyClass];
    const skillLatency = LATENCY_ORDER[skill.latency_class];
    if (skillLatency > allowed) score -= 0.5;
  }

  if (ctx.budgetConstraints?.costClass) {
    const allowed = COST_ORDER[ctx.budgetConstraints.costClass];
    const skillCost = COST_ORDER[skill.cost_class];
    if (skillCost > allowed) score -= 0.5;
  }

  return Math.max(0, score);
}

const LATENCY_ORDER = { fast: 0, normal: 1, slow: 2 };
const COST_ORDER    = { low: 0, normal: 1, high: 2 };
```

---

## 6. Latency Fit / Cost Fit (w5, w6)

```typescript
function latencyFitScore(skill: SkillMeta, ctx: RouterContext): number {
  if (!ctx.budgetConstraints?.latencyClass) return 1.0; // 제약 없음
  const req = LATENCY_ORDER[ctx.budgetConstraints.latencyClass];
  const sk  = LATENCY_ORDER[skill.latency_class];
  return sk <= req ? 1.0 : 0.0;
}

function costFitScore(skill: SkillMeta, ctx: RouterContext): number {
  if (!ctx.budgetConstraints?.costClass) return 1.0;
  const req = COST_ORDER[ctx.budgetConstraints.costClass];
  const sk  = COST_ORDER[skill.cost_class];
  return sk <= req ? 1.0 : 0.0;
}
```

---

## 7. 가중치 튜닝 계획

### 7.1 튜닝 주기: 매주 (Phase 4 ~)

```
golden_tasks (30개) 실행
    │
    ▼
precision = top1_correct / 30
    │
    ▼
if precision < 0.85:
  run weight_optimizer (grid search on w1~w6)
    │
    ▼
update .omc/registry/weights.json
```

### 7.2 가중치 저장

```json
// .omc/registry/weights.json
{
  "version": "1.0.0",
  "updated_at": "2026-03-05",
  "weights": {
    "w1_intent_match": 0.35,
    "w2_vector_similarity": 0.25,
    "w3_quality_score": 0.15,
    "w4_policy_fit": 0.10,
    "w5_latency_fit": 0.08,
    "w6_cost_fit": 0.07
  },
  "penalties": {
    "conflict": -0.30,
    "deprecated": -0.50,
    "high_risk_no_approval": -0.80,
    "budget_exceeded": -0.20
  }
}
```

---

## 8. Golden Tasks (30개 기준)

30개 정의 원칙:

| 카테고리 | 개수 | 예시 |
|---------|------|------|
| 디버깅 | 6 | "파이썬 에러 고쳐줘", "타입스크립트 빌드 실패" |
| 기획/설계 | 5 | "REST API 설계해줘", "프로젝트 기획" |
| 코드 품질 | 5 | "코드 리뷰 해줘", "리팩토링" |
| 검색/탐색 | 4 | "파일에서 X 찾아줘" |
| 보안 | 3 | "취약점 검사", "SQL injection 확인" |
| 테스트 | 3 | "TDD로 구현", "테스트 작성" |
| 애매한 요청 | 4 | "이거 고쳐줘" (ambiguous 처리 검증) |

각 태스크에 `expected_skill_id`와 `acceptable_skills[]` 정의.
