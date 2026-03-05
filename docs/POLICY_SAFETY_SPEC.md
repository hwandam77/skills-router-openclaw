# Policy & Safety 상세 Spec (v1)

작성일: 2026-03-05

---

## 1. 정책 엔진 구조

```
요청 수신
    │
    ▼
[Stage A Filter]  → status/tools/risk 하드 필터
    │
    ▼
[Stage B Rank]    → 점수 기반 Top-K 선택
    │
    ▼
[Policy Engine]   → 최종 허용/차단 결정
    │
    ├── ALLOW  → Executor로 전달
    └── DENY   → 차단 사유 반환 + 대안 제시
```

---

## 2. Risk Level 정의

| risk_level | 의미 | 예시 스킬 | 처리 방식 |
|-----------|------|---------|---------|
| `low` | 읽기/분석 전용, 부수효과 없음 | `analyze`, `deepsearch`, `code-review` | 자동 허용 |
| `medium` | 파일/코드 변경, 로컬 영향 | `executor`, `tdd`, `build-fix` | 자동 허용 (budget 확인) |
| `high` | 외부 전송, 파괴적 명령, 원격 실행 | `release`, `git-master` (force push), `mcp-setup` | **approval token 필수** |

---

## 3. Approval Token 플로우 (high-risk)

### 3.1 플로우 다이어그램

```
사용자 요청 (고위험 스킬 필요)
    │
    ▼
Policy Engine: risk_level == 'high' AND approvalToken 없음
    │
    ▼
[Approval Gate] 사용자에게 확인 요청:
    "⚠️  이 작업은 고위험 작업입니다: [skillId]
     작업 내용: [description]
     외부 영향: [external_impact]
     계속하시겠습니까?"
    │
    ├── 사용자 거부 → DENY (reason: user_rejected)
    │
    └── 사용자 승인
            │
            ▼
        approvalToken 발행:
        {
          token: UUID v4,
          skillId: string,
          issuedAt: ISO 8601,
          expiresAt: issuedAt + 5min,
          issuedFor: runId
        }
            │
            ▼
        token을 RouterContext.approvalToken에 주입
            │
            ▼
        Policy Engine 재검사 → ALLOW
```

### 3.2 Token 검증

```typescript
interface ApprovalToken {
  token: string;       // UUID v4
  skillId: string;
  issuedAt: string;    // ISO 8601
  expiresAt: string;   // issuedAt + 5분
  issuedFor: string;   // runId
}

function validateApprovalToken(
  token: ApprovalToken,
  skillId: string,
  runId: string
): { valid: boolean; reason?: string } {
  if (token.skillId !== skillId)
    return { valid: false, reason: 'skill_mismatch' };
  if (token.issuedFor !== runId)
    return { valid: false, reason: 'run_mismatch' };
  if (new Date() > new Date(token.expiresAt))
    return { valid: false, reason: 'token_expired' };
  return { valid: true };
}
```

### 3.3 Approval Gate 메시지 형식

```
⚠️  고위험 작업 확인 필요

스킬: release (v1.2.0)
설명: NPM 패키지를 공개 레지스트리에 배포합니다.
외부 영향: 퍼블릭 NPM 레지스트리에 영구 게시
되돌리기: 불가능 (deprecate만 가능)

[Y] 승인하고 계속  [N] 취소
```

---

## 4. External-Send / Destructive 차단 규칙

특정 행동 패턴은 skill risk_level과 무관하게 policy-gated:

```typescript
const ALWAYS_GATED_PATTERNS = [
  'git push --force',
  'git push --force-with-lease',
  'npm publish',
  'rm -rf',
  'DROP TABLE',
  'DELETE FROM',   // WHERE 없는 경우
  'send_email',
  'send_slack',    // 외부 메시지 전송
];

function detectGatedPattern(command: string): boolean {
  return ALWAYS_GATED_PATTERNS.some(p => command.includes(p));
}
```

이 패턴이 감지되면 approval token 없이는 실행 불가.

---

## 5. Multi-Agent Safety

### 5.1 서브에이전트별 Tool Allowlist

```typescript
const AGENT_TOOL_ALLOWLIST: Record<string, string[]> = {
  'executor-low':    ['read', 'edit', 'write'],
  'executor':        ['read', 'edit', 'write', 'exec'],
  'executor-high':   ['read', 'edit', 'write', 'exec', 'bash'],
  'researcher':      ['read', 'web_search', 'fetch'],
  'explore':         ['read', 'glob', 'grep'],
  'architect':       ['read', 'glob', 'grep', 'write'],
  // ... 기타 에이전트
};

function enforceToolAllowlist(agentType: string, requestedTool: string): boolean {
  const allowed = AGENT_TOOL_ALLOWLIST[agentType] ?? [];
  return allowed.includes(requestedTool);
}
```

### 5.2 Run Budget 강제

```typescript
interface RunBudget {
  maxSteps: number;      // 기본 10, 실행 단계 수
  maxTimeMs: number;     // 기본 30_000 ms
  maxCostTokens: number; // 기본 50_000 tokens (추정)
}

const DEFAULT_BUDGET: Record<string, RunBudget> = {
  low:    { maxSteps: 5,  maxTimeMs: 10_000, maxCostTokens: 10_000 },
  normal: { maxSteps: 10, maxTimeMs: 30_000, maxCostTokens: 50_000 },
  high:   { maxSteps: 30, maxTimeMs: 120_000, maxCostTokens: 200_000 },
};
```

### 5.3 동일 실패 2회 → 전략 변경

```typescript
interface FailureTracker {
  skillId: string;
  failCount: number;
  lastFailClass: FailClass;
  lastFailAt: string;
}

function onSkillFail(tracker: FailureTracker, runId: string): StrategyChange {
  if (tracker.failCount >= 2) {
    return {
      action: 'change_strategy',
      options: [
        'reduce_scope_50pct',   // 작업 범위 절반으로 축소
        'fallback_skill',       // 다음 Top-K 스킬로 전환
        'halt_and_report',      // 실행 중단 + 사용자에게 보고
      ],
      blockedSkill: tracker.skillId,
      blockDurationMs: 5 * 60 * 1000, // 5분 circuit break
    };
  }
  return { action: 'retry' };
}
```

---

## 6. Shadow Mode (Phase 1 A/B 비교)

### 6.1 동작 방식

```
사용자 요청
    │
    ├── [기존 라우팅] → 실제 실행 (프로덕션)
    │
    └── [신규 Router] → 결과만 기록 (실행 안 함)
            │
            ▼
        ShadowComparison 로그에 기록
```

### 6.2 Shadow 비교 결과 구조

```typescript
interface ShadowComparison {
  runId: string;
  timestamp: string;
  userIntent: string;

  legacy: {
    selected: string[];      // 기존 라우팅이 선택한 스킬들
  };
  router: {
    selected: string[];      // 신규 라우터가 선택한 스킬들
    scores: Record<string, number>;
    latencyMs: number;
  };

  comparison: {
    top1Match: boolean;                // Top-1 일치 여부
    overlapRate: number;               // 0.0~1.0
    diverged: boolean;
    divergenceReason?: string;         // 왜 다른 선택을 했는지
  };
}
```

### 6.3 Shadow 모드 활성화 조건

```typescript
// .omc/registry/config.json
{
  "shadowMode": {
    "enabled": true,              // Phase 1에서 true
    "sampleRate": 1.0,            // 100% 요청에 대해 shadow 실행
    "logPath": ".omc/logs/shadow-comparisons.jsonl"
  }
}
```

### 6.4 Shadow 리포트 (주간)

```
Shadow Mode Report (2026-W10)
─────────────────────────────
총 요청: 284
Top-1 일치율: 78.5%  (목표: 85%+)
주요 불일치:
  - "코드 리뷰" → 기존: code-review / 신규: systematic-debugging (12회)
  - "배포해줘"  → 기존: release     / 신규: git-master (8회)
권장 조치:
  - intent-dict.yml에 "코드 리뷰" → code-review 명시적 매핑 추가
  - release 스킬 intents에 "배포" 추가
```

---

## 7. 정책 차단 이벤트 로그

```jsonc
// .omc/logs/policy-events.jsonl
{
  "eventId": "pe-001",
  "ts": "2026-03-05T11:00:00Z",
  "runId": "abc123",
  "type": "high_risk_blocked",
  "skillId": "release",
  "reason": "approval_token_missing",
  "userIntent": "지금 바로 배포해줘",
  "resolved": false
}

{
  "eventId": "pe-002",
  "ts": "2026-03-05T11:05:00Z",
  "runId": "abc456",
  "type": "circuit_break",
  "skillId": "build-fix",
  "reason": "same_failure_twice",
  "failClass": "tool_fail",
  "blockedUntil": "2026-03-05T11:10:00Z"
}
```

---

## 8. Policy Violation SLO

| 메트릭 | 목표 |
|-------|------|
| policy_violation_leakage | = 0 (high-risk 무승인 실행 0건) |
| approval_gate_latency_p50 | < 3초 (사용자 응답 포함) |
| circuit_break_recovery_rate | >= 70% |
| shadow_top1_agreement | >= 85% (Phase 2 전환 기준) |
