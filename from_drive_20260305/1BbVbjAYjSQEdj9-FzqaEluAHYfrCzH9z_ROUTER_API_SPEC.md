# Router API Interface Spec (v1)

작성일: 2026-03-05

---

## 1. 핵심 타입 정의

```typescript
// src/router/types.ts

// ─── 입력 ──────────────────────────────────────────────────────────────────

export interface RouterContext {
  userIntent: string;              // 사용자 자연어 요청
  conversationHistory?: Message[]; // 최근 N턴 대화 (옵션)
  availableTools: string[];        // 현재 환경에서 사용 가능한 툴 목록
  budgetConstraints?: BudgetConstraints;
  approvalToken?: string;          // high-risk 승인 시 제공
  mode?: 'normal' | 'shadow';     // shadow 모드 여부
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface BudgetConstraints {
  maxSteps?: number;       // 기본 10
  maxTimeMs?: number;      // 기본 30000 (30초)
  latencyClass?: 'fast' | 'normal' | 'slow';  // 허용 latency
  costClass?: 'low' | 'normal' | 'high';      // 허용 cost
}

// ─── 출력 ──────────────────────────────────────────────────────────────────

export interface RouterResult {
  runId: string;          // UUID v4
  traceId: string;        // UUID v4 (parent trace)
  timestamp: string;      // ISO 8601

  // 선택 결과
  selected: SkillCandidate[];           // Top-K 최종 선택
  shortlisted: SkillCandidate[];        // Stage B 후보 전체 (로그용)
  rejected: RejectedSkill[];            // 필터에서 탈락한 스킬

  // 실행 메타
  stageLatencyMs: {
    stageA: number;
    stageB: number;
    total: number;
  };

  // 정책 결정
  policyDecision: PolicyDecision;

  // 실패 분류 (선택 실패 시)
  failClass?: FailClass;
  outcome: 'success' | 'fail' | 'partial';
}

export interface SkillCandidate {
  skillId: string;
  version: string;
  score: number;           // 0.0 ~ 1.0
  scoreBreakdown: ScoreBreakdown;
  selectionReason: string; // 자연어 설명 (로그/설명가능성용)
  rank: number;            // 1-based
}

export interface ScoreBreakdown {
  intentMatch: number;      // w1
  vectorSimilarity: number; // w2
  qualityScore: number;     // w3
  policyFit: number;        // w4
  latencyFit: number;       // w5
  costFit: number;          // w6
  penalties: PenaltyDetail[];
  total: number;
}

export interface PenaltyDetail {
  type: 'conflict' | 'deprecated' | 'high_risk_no_approval' | 'budget_exceeded';
  value: number;  // 음수
  reason: string;
}

export interface RejectedSkill {
  skillId: string;
  stage: 'A' | 'B';
  reason: string;  // 탈락 사유
}

export interface PolicyDecision {
  allowed: boolean;
  requiresApproval: boolean;
  approvalGranted: boolean;
  blockedReason?: string;
}

export type FailClass =
  | 'context_miss'       // 의도 파악 실패
  | 'tool_fail'          // 필요 툴 없음
  | 'validation_fail'    // 스킬 메타 유효성 실패
  | 'timeout'            // 라우팅 타임아웃
  | 'policy_block';      // 정책 차단
```

---

## 2. Router 함수 시그니처

```typescript
// src/router/index.ts

export interface SkillRouter {
  /**
   * 메인 라우팅 함수
   * - Stage A: 필터 (status/tools/risk/conflicts)
   * - Stage B: 랭킹 (scoring)
   * - Policy: 최종 승인 여부 결정
   */
  select(context: RouterContext): Promise<RouterResult>;

  /**
   * Stage A만 실행 (테스트/디버깅용)
   */
  filter(context: RouterContext): Promise<SkillCandidate[]>;

  /**
   * Stage B만 실행 (테스트/디버깅용)
   * @param candidates Stage A 결과
   */
  rank(context: RouterContext, candidates: SkillCandidate[]): Promise<SkillCandidate[]>;

  /**
   * Shadow 모드: 기존 라우팅과 병행 실행 후 결과 비교 로그
   * - 실제 실행은 기존 방식으로 수행
   * - 본 라우터 결과는 로그에만 기록
   */
  shadow(context: RouterContext, legacySelected: string[]): Promise<ShadowComparison>;
}

export interface ShadowComparison {
  runId: string;
  legacySelected: string[];
  routerSelected: string[];
  agreement: boolean;       // Top-1 일치 여부
  agreementRate: number;    // Top-K 일치율 (0.0~1.0)
  divergenceReason?: string;
}
```

---

## 3. 호출 예시

```typescript
// 기본 사용
const router = createRouter({ registry, config });

const result = await router.select({
  userIntent: "파이썬 타입 에러 디버깅해줘",
  availableTools: ["exec", "read", "edit"],
  budgetConstraints: { latencyClass: "fast", costClass: "low" }
});

console.log(result.selected[0].skillId);        // "systematic-debugging"
console.log(result.selected[0].selectionReason); // "intent 'debug' 매칭, quality 0.88"

// Shadow 모드 (Phase 1 A/B 비교)
const shadow = await router.shadow(ctx, ["old-skill-id"]);
console.log(shadow.agreement); // true/false
```

---

## 4. 에러 처리

| 에러 상황 | 동작 |
|----------|------|
| Registry 비어있음 | `FailClass: 'validation_fail'` + fallback 안내 |
| 후보 0개 (Stage A) | `FailClass: 'context_miss'` + 의도 재해석 시도 |
| 라우팅 타임아웃 | `FailClass: 'timeout'` + 마지막 partial 결과 반환 |
| 정책 차단 | `FailClass: 'policy_block'` + 차단 사유 포함 |

---

## 5. Top-K 결정 규칙

```typescript
function determineTopK(intent: ParsedIntent): number {
  if (intent.isComposite) return 3;   // "이거랑 저거 같이 해줘"
  if (intent.isAmbiguous) return 2;   // 의도 불명확
  return 1;                            // 단일 명확 요청
}
```

---

## 6. 로그 출력 포맷

```jsonc
// .omc/logs/router-trace.jsonl (append-only)
{
  "runId": "a1b2c3d4",
  "traceId": "e5f6g7h8",
  "ts": "2026-03-05T10:30:00Z",
  "intent": "파이썬 타입 에러 디버깅해줘",
  "stageA_filtered_in": 12,
  "stageA_filtered_out": 388,
  "selected": [{"skillId": "systematic-debugging", "score": 0.91}],
  "rejected": [{"skillId": "security-review", "stage": "A", "reason": "domain mismatch"}],
  "latency": {"stageA": 45, "stageB": 120, "total": 165},
  "outcome": "success"
}
```
