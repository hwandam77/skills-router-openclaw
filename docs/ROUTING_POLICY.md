# Routing Policy (v2)

**작성일:** 2026-03-05  
**최종 업데이트:** 2026-03-05 (OpenClaw 벤치마킹 반영)  
**버전:** 2.0

---

## 📌 개요

Routing Policy v2 는 Skill Router v1 Plan 과 Skill Registry Schema v2 에 기반하여, 안전하고 효율적이며 설명 가능한 스킬 라우팅을 정의합니다.

**주요 변화:**
- ✨ **Installation Check** 필터 추가
- 📊 **Health Metrics** 기반 동적 스코어링
- 🎯 **Context-Aware** 필터링 (채널/권한/세션)
- 🤖 **Model Fit** 최적화
- 🔒 **Enhanced Approval Flow** 강화

---

## 🚦 Stage A: Filter (Hard Constraints)

Stage A 는 반드시 충족해야 하는硬性 제약사항을 적용합니다. 이 단계를 통과하지 못한 스킬은 후보에서 즉시 배제됩니다.

### 1. **Status Filter**

```typescript
if (skill.status !== 'active') {
  reject('Status not active');
}
```

- ✅ `active`: 정상 사용 가능
- ❌ `deprecated`: 기본 배제 (명시적 override 필요)
- ⚠️ `experimental`: 실험적, 높은 실패 리스크

**Override 규칙:**
- `allowDeprecated=true` 설정 시 deprecated 스킬도 후보에 포함
- 명시적 `skill_id` 지정 시 experimental 스킬도 사용 가능

---

### 2. **Installation & Dependency Check** (New in v2)

```typescript
// 1. 필수 의존성 설치 확인
for (const install of skill.install) {
  if (install.required && !isInstalled(install)) {
    reject(`Required tool not installed: ${install.label}`);
  }
}

// 2. 환경 검증 명령어 실행
for (const check of skill.environment_checks) {
  const result = await executeCommand(check.command, {
    timeout: check.timeout_ms ?? 5000
  });
  if (!result.success) {
    reject(check.error_message);
    suggest(check.fallback_suggestion);
  }
}
```

**결론:**
- ✅ 설치됨: 후보 유지
- ⚠️ 설치 불필요: 후보 유지 (install[].required=false)
- ❌ 설치됨 없음: 후보 배제 + 대체 스킬 제안

---

### 3. **Required Tools Availability**

```typescript
const unavailable = skill.required_tools.filter(
  tool => !context.availableTools.includes(tool)
);
if (unavailable.length > 0) {
  reject(`Tools unavailable: ${unavailable.join(', ')}`);
}
```

**예시:**
- 스킬 필요: `["exec", "read", "gh"]`
- 사용 가능: `["exec", "read"]`
- 결과: ❌ 배제 (`gh` unavailable)

---

### 4. **Risk Guardrail**

```typescript
if (skill.risk_level === 'high') {
  if (!context.approvalToken) {
    reject('High-risk skill requires approval token');
    markRequiresApproval(skill.skill_id);
    return; // 최종 선택 전에 추가 승인 필요
  }
  if (!validateApprovalToken(context.approvalToken, skill.skill_id)) {
    reject('Invalid or expired approval token');
  }
}
```

**Risk Level 정의:**

| 수준 | 예시 | 정책 |
|------|------|------|
| `low` | 정보 조회, 분석 | 자동 허용 |
| `medium` | 파일 수정, 일반 API 호출 | 로그 기록 |
| `high` | 외부 전송, 파괴적 명령 | 승인 필요 |

---

### 5. **Conflict & Dependency Constraints**

```typescript
// 충돌 확인
for (const conflictId of skill.conflicts) {
  if (context.selectedSkills.includes(conflictId)) {
    reject(`Conflicts with already selected skill: ${conflictId}`);
  }
}

// 의존성 확인
for (const depId of skill.dependencies) {
  if (!context.selectedSkills.includes(depId)) {
    // 의존 스킬이 선택되지 않았으면 추가하거나 배제
    if (!canAddSkill(depId)) {
      reject(`Dependency not satisfied: ${depId}`);
    }
  }
}
```

---

### 6. **Context-Aware Filter** (New in v2)

```typescript
// 채널 가용성 확인
if (skill.available_in?.channels) {
  if (!skill.available_in.channels.includes(context.channel)) {
    reject(`Not available in channel: ${context.channel}`);
  }
}

// 그룹 채널 정책
if (context.isGroup && skill.available_in?.group_policy === 'deny') {
  reject('Blocked in group channels');
}
if (context.isGroup && skill.available_in?.group_policy === 'require_mention') {
  if (!context.isUserMention) {
    reject('Requires mention in group channels');
  }
}

// 권한 확인
for (const perm of skill.permissions_required) {
  if (!context.userPermissions.includes(perm.permission)) {
    reject(`Missing permission: ${perm.permission}`);
  }
  if (perm.requires_approval && !context.approvalToken) {
    reject(`Approval required for: ${perm.permission}`);
  }
}
```

---

### 7. **Budget Constraints**

```typescript
if (context.budgetConstraints) {
  const { latencyClass, costClass } = context.budgetConstraints;
  
  if (latencyClass && skill.latency_class === 'slow') {
    reject('Latency class exceeds budget (slow)');
  }
  
  if (costClass && skill.cost_class === 'high') {
    reject('Cost class exceeds budget (high)');
  }
}
```

---

## 📈 Stage B: Rank (Soft Scoring)

Stage A 를 통과한 후보들에 대해 점수화된 랭킹을 적용합니다.

### **Scoring Formula (v2)**

```
S = w1*intent_match 
    + w2*vector_similarity 
    + w3*quality_score 
    + w4*policy_fit 
    + w5*latency_fit 
    + w6*cost_fit 
    + w7*model_fit 
    + w8*context_bonus
    - w9*health_penalty
    - penalties
```

### **Weight Defaults**

| 가중치 | 기본값 | 설명 |
|--------|--------|------|
| w1 | 0.25 | 의도 매칭 (가장 중요) |
| w2 | 0.20 | 벡터 유사도 |
| w3 | 0.15 | 품질 점수 |
| w4 | 0.10 | 정책 적합도 |
| w5 | 0.10 | 지연 시간 적합도 |
| w6 | 0.05 | 비용 적합도 |
| w7 | 0.05 | 모델 적합도 |
| w8 | 0.05 | 컨텍스트 보너스 |
| w9 | 0.15 | 건강 패널티 |

---

### **Component Scoring Details**

#### 1. **Intent Match (0.0 ~ 1.0)**

```typescript
function scoreIntentMatch(userIntent: string, skill: Skill): number {
  // 1. 명시적 intent 매칭
  const directMatch = skill.intents.some(intent => 
    userIntent.toLowerCase().includes(intent)
  );
  if (directMatch) return 1.0;
  
  // 2. 의미론적 매칭 (LLM 또는 embedding)
  const semanticScore = cosineSimilarity(
    embedding(userIntent),
    embedding(skill.description)
  );
  return semanticScore;
}
```

---

#### 2. **Vector Similarity (0.0 ~ 1.0)**

```typescript
function scoreVectorSimilarity(
  userIntent: string, 
  skill: Skill
): number {
  return cosineSimilarity(
    embedding(userIntent),
    skill.embedding // 사전 계산된 스킬 임베딩
  );
}
```

---

#### 3. **Quality Score (0.0 ~ 1.0)**

```typescript
function scoreQuality(skill: Skill): number {
  return skill.quality_score; // Registry 에서 직접 사용
}
```

---

#### 4. **Policy Fit (0.0 ~ 1.0)**

```typescript
function scorePolicyFit(skill: Skill, context: RouterContext): number {
  let score = 1.0;
  
  // 위험 수준 보정
  if (skill.risk_level === 'high' && context.approvalToken) {
    score += 0.1; // 승인된 high-risk 에 보너스
  }
  
  // 채널 정책 일치
  if (skill.available_in?.channels.includes(context.channel)) {
    score += 0.05;
  }
  
  return Math.min(score, 1.0);
}
```

---

#### 5. **Latency Fit (0.0 ~ 1.0)**

```typescript
function scoreLatencyFit(
  skill: Skill, 
  context: RouterContext
): number {
  if (!context.budgetConstraints?.latencyClass) {
    return 1.0; // 제약 없음
  }
  
  const { latencyClass } = context.budgetConstraints;
  const skillLatency = skill.latency_class;
  
  // budget 보다 빠른 경우 보너스
  if (latencyClass === 'fast' && skillLatency === 'fast') {
    return 1.0;
  }
  if (latencyClass === 'fast' && skillLatency !== 'fast') {
    return 0.5; // 불일치 패널티
  }
  if (latencyClass === 'normal' && skillLatency === 'slow') {
    return 0.6; // 약간 느림
  }
  
  return 0.8; // 기본 일치
}
```

---

#### 6. **Cost Fit (0.0 ~ 1.0)**

```typescript
function scoreCostFit(
  skill: Skill, 
  context: RouterContext
): number {
  if (!context.budgetConstraints?.costClass) {
    return 1.0;
  }
  
  const { costClass } = context.budgetConstraints;
  
  if (costClass === 'low' && skill.cost_class !== 'low') {
    return 0.6; // 비용 초과
  }
  if (costClass === 'low' && skill.cost_class === 'low') {
    return 1.0;
  }
  
  return 0.9; // 기본 일치
}
```

---

#### 7. **Model Fit (New in v2) (0.0 ~ 1.0)**

```typescript
function scoreModelFit(skill: Skill, currentModel: Model): number {
  // 1. 선호 모델 일치
  if (skill.preferred_models?.some(m => m.model_id === currentModel.id)) {
    return 1.0;
  }
  
  // 2. 모델 강점 매칭
  const modelStrengths = currentModel.strengths || [];
  const skillStrengths = skill.model_strengths?.strengths || [];
  const matchRate = skillStrengths.filter(s => 
    modelStrengths.includes(s)
  ).length / skillStrengths.length;
  
  return matchRate;
}
```

---

#### 8. **Context Bonus (New in v2) (-0.2 ~ 0.15)**

```typescript
function scoreContextBonus(
  skill: Skill, 
  context: RouterContext
): number {
  let bonus = 0.0;
  
  // 채널 일치 보너스
  if (skill.available_in?.channels.includes(context.channel)) {
    bonus += 0.1;
  }
  
  // 권한 충족 보너스
  const hasAllPermissions = skill.permissions_required?.every(
    perm => context.userPermissions.includes(perm.permission)
  );
  if (hasAllPermissions) {
    bonus += 0.05;
  }
  
  // 설치 완료 보너스
  if (skill.install?.every(inst => isInstalled(inst))) {
    bonus += 0.05;
  }
  
  return Math.max(bonus, -0.2); // 최소 -0.2 (권한 부족 등)
}
```

---

#### 9. **Health Penalty (New in v2) (0.0 ~ 0.3)**

```typescript
function calculateHealthPenalty(skill: Skill): number {
  const metrics = skill.metrics;
  if (!metrics) return 0.0;
  
  let penalty = 0.0;
  
  // 최근 실패율 패널티
  if (metrics.success_rate_7d < 0.8) {
    penalty += (1.0 - metrics.success_rate_7d) * 0.3;
  }
  
  // 지연 시간 악화 패널티
  if (metrics.avg_latency_ms > 500) {
    penalty += Math.min(0.1, (metrics.avg_latency_ms - 500) / 5000);
  }
  
  // 연속 실패 패널티
  if (metrics.consecutive_failures > 0) {
    penalty += Math.min(0.15, metrics.consecutive_failures * 0.05);
  }
  
  return Math.min(penalty, 0.3); // 최대 0.3
}
```

---

#### 10. **Penalties**

```typescript
function calculatePenalties(skill: Skill, context: RouterContext): number {
  let penalties = 0.0;
  
  // 충돌 패널티
  if (skill.conflicts.length > 0) {
    penalties += 0.1;
  }
  
  // deprecated 패널티
  if (skill.status === 'deprecated') {
    penalties += 0.5; // 매우 큼
  }
  
  // high-risk without approval
  if (skill.risk_level === 'high' && !context.approvalToken) {
    penalties += 1.0; // 배제 수준
  }
  
  // 환경 불일치
  if (!skill.environment_checks?.every(check => check.success)) {
    penalties += 0.3;
  }
  
  return penalties;
}
```

---

## 🎯 Selection (Top-K 결정)

### **Top-K 규칙**

```typescript
function determineTopK(request: Request): number {
  // 1. 의도 복잡도 분석
  if (request.isComposite) {
    // "이거랑 저거 같이 해줘"
    return 3;
  }
  
  if (request.isAmbiguous) {
    // 의도 불명확
    return 2;
  }
  
  // 2. 예산 제약
  if (request.budgetConstraints?.maxSkills) {
    return request.budgetConstraints.maxSkills;
  }
  
  // 3. 기본값
  return 1;
}
```

### **Selection Logic**

```typescript
function selectTopK(candidates: RankedSkill[], k: number): SkillCandidate[] {
  const sorted = candidates.sort((a, b) => b.score - a.score);
  const selected = sorted.slice(0, k);
  
  // 충돌 제거 후 재선택
  const final = removeConflicts(selected);
  if (final.length < k) {
    // 추가 후보 채우기
    const remaining = candidates.filter(
      c => !final.some(f => f.skill_id === c.skill_id)
    );
    final.push(...remaining.slice(0, k - final.length));
  }
  
  return final;
}
```

---

## 🛡️ Safety & Guardrails

### **1. High-Risk Approval Flow**

```typescript
async function requestApproval(skill: Skill, context: RouterContext): Promise<boolean> {
  const approvalRequest = {
    requestId: uuidv4(),
    skillId: skill.skill_id,
    riskReason: getRiskReason(skill),
    requestedAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString() // 30 분
  };
  
  // 승인 요청 전송
  await sendApprovalNotification(approvalRequest);
  
  // 승인 대기
  const approval = await waitForApproval(approvalRequest.requestId, {
    timeout: 30 * 60 * 1000 // 30 분
  });
  
  if (approval.granted) {
    context.approvalToken = approval.token;
    return true;
  }
  
  return false;
}
```

---

### **2. External-Send / Destructive Actions**

```typescript
const RESTRICTED_ACTIONS = [
  'external_send',
  'destructive',
  'mass_update',
  'financial_transfer'
];

function checkRestrictedActions(skill: Skill): PolicyDecision {
  const actions = skill.capabilities || [];
  const restricted = actions.filter(a => RESTRICTED_ACTIONS.includes(a));
  
  if (restricted.length > 0) {
    return {
      allowed: false,
      requiresApproval: true,
      blockedReason: `Restricted actions: ${restricted.join(', ')}`,
      restrictedActions: restricted
    };
  }
  
  return { allowed: true, requiresApproval: false };
}
```

---

### **3. Failure Recovery Strategy**

```typescript
function handleFailure(failure: FailureEvent): RecoveryAction {
  const failureCount = getFailureCount(failure.skillId);
  
  if (failureCount === 1) {
    // 첫 번째 실패: 재시도
    return {
      action: 'retry',
      maxRetries: 2,
      backoffMs: 1000
    };
  }
  
  if (failureCount === 2) {
    // 두 번째 실패: 전략 변경
    return {
      action: 'change_strategy',
      suggestion: 'Use alternative skill or reduce scope by 50%'
    };
  }
  
  if (failureCount >= 3) {
    // 세 번째 실패: 중단 및 대체 제안
    const alternatives = findAlternativeSkills(failure.skillId);
    return {
      action: 'stop_and_suggest',
      alternatives: alternatives,
      failureClass: failure.class
    };
  }
}
```

---

### **4. Circuit Breaker**

```typescript
interface CircuitBreaker {
  failureCount: number;
  lastFailureTime: Date;
  state: 'closed' | 'open' | 'half-open';
}

function checkCircuitBreaker(skill: Skill): boolean {
  const breaker = getCircuitBreaker(skill.skill_id);
  
  if (breaker.state === 'open') {
    // 1 분 후 재시도
    if (Date.now() - breaker.lastFailureTime.getTime() > 60000) {
      breaker.state = 'half-open';
      return true; // 재시도 허용
    }
    return false; // 차단됨
  }
  
  return true; // 정상
}

function recordFailure(skillId: string) {
  const breaker = getCircuitBreaker(skillId);
  breaker.failureCount++;
  breaker.lastFailureTime = new Date();
  
  if (breaker.failureCount >= 5) {
    breaker.state = 'open';
  }
}
```

---

## 🔄 Fallback & Substitution

### **1. Auto-Substitution Logic**

```typescript
function findSubstitute(failedSkill: Skill, context: RouterContext): Skill | null {
  // 1. 대체 스킬 명시
  if (failedSkill.compatibility?.replaced_by) {
    const replacement = getSkillById(failedSkill.compatibility.replaced_by);
    if (canUseSkill(replacement, context)) {
      return replacement;
    }
  }
  
  // 2. 유사 스킬 검색 (동일 domain + intents)
  const similar = searchSkills({
    domain: failedSkill.domain,
    intents: failedSkill.intents,
    exclude: [failedSkill.skill_id]
  });
  
  // 3. 점수 기반 상위 선택
  const ranked = similar.map(skill => ({
    skill,
    score: calculateSubstitutionScore(skill, failedSkill)
  })).sort((a, b) => b.score - a.score);
  
  if (ranked.length > 0 && ranked[0].score > 0.7) {
    return ranked[0].skill;
  }
  
  return null;
}

function calculateSubstitutionScore(
  candidate: Skill, 
  original: Skill
): number {
  let score = 0.0;
  
  // Intent 일치 (가중치 0.5)
  const intentOverlap = candidate.intents.filter(i => 
    original.intents.includes(i)
  ).length / original.intents.length;
  score += intentOverlap * 0.5;
  
  // Domain 일치 (가중치 0.3)
  if (candidate.domain === original.domain) {
    score += 0.3;
  }
  
  // 품질 점수 (가중치 0.2)
  score += candidate.quality_score * 0.2;
  
  return score;
}
```

---

## 📊 Shadow Mode (A/B Testing)

```typescript
interface ShadowComparison {
  runId: string;
  legacySelected: string[];
  routerSelected: string[];
  agreement: boolean;       // Top-1 일치
  agreementRate: number;    // Top-K 일치율 (0.0~1.0)
  divergenceReason?: string;
  legacyLatencyMs: number;
  routerLatencyMs: number;
}

async function runShadowMode(
  context: RouterContext,
  legacySelection: string[]
): Promise<ShadowComparison> {
  const runId = uuidv4();
  
  // 새 라우터로 선행
  const routerResult = await router.select(context);
  const routerSelected = routerResult.selected.map(s => s.skillId);
  
  // 비교
  const agreement = legacySelection[0] === routerSelected[0];
  const agreementRate = calculateAgreementRate(legacySelection, routerSelected);
  
  // 차이버 사유 분석
  let divergenceReason: string | undefined;
  if (!agreement) {
    divergenceReason = analyzeDivergenceReason(legacySelection, routerSelected);
  }
  
  // 로그 기록
  logShadowComparison({
    runId,
    legacySelected,
    routerSelected,
    agreement,
    agreementRate,
    divergenceReason,
    legacyLatencyMs: context.legacyLatency,
    routerLatencyMs: routerResult.stageLatencyMs.total
  });
  
  return {
    runId,
    legacySelected,
    routerSelected,
    agreement,
    agreementRate,
    divergenceReason
  };
}
```

---

## 📋 Summary

| 단계 | 목적 | 통과율 (예시) |
|------|------|---------------|
| **Stage A** |硬性 제약 필터링 | 400 → 20 |
| **Stage B** | 점수 기반 랭킹 | 20 → 5 |
| **Selection** | Top-K 결정 | 5 → 1~3 |
| **Safety** | 최종 검증 | 1~3 → 1~3 |
| **Fallback** | 실패 시 대체 | - |

**전체 처리 시간 목표:**
- Stage A: < 100ms
- Stage B: < 200ms
- Total: < 300ms (P50), < 1200ms (P95)

---

## 📚 References

- [SKILL_ROUTER_V1_PLAN.md](SKILL_ROUTER_V1_PLAN.md)
- [SKILL_REGISTRY_SCHEMA.md](SKILL_REGISTRY_SCHEMA.md)
- [ROUTER_API_SPEC.md](ROUTER_API_SPEC.md)
- [OpenClaw Security](https://docs.openclaw.ai/gateway/security)
```

ROUTING_POLICY.md 가 v2 로 성공적으로 업데이트되었습니다! 주요 변경 내용은 다음과 같습니다:

## ✨ 추가된 내용

1. **Installation & Dependency Check**: 의존성 설치 및 환경 검증 필터 추가
2. **Context-Aware Filter**: 채널/권한/세션 기반 필터링
3. **Health Penalty**: 실시간 실패율/지연 시간 기반 패널티
4. **Model Fit**: 모델 적합도 스코어링
5. **Enhanced Approval Flow**: 고위험 스킬 승인 워크플로우 상세화
6. **Circuit Breaker**: 연속 실패 시 자동 차단
7. **Auto-Substitution**: 실패 시 대체 스킬 자동 제안
8. **Shadow Mode**: A/B 테스트 비교 기능
9. **성능 메트릭**: 각 단계별 처리 시간 목표 명시
