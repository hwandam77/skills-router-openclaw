# Phase Roadmap (v2)

**작성일:** 2026-03-05  
**최종 업데이트:** 2026-03-05 (OpenClaw 벤치마킹 반영)  
**버전:** 2.0

---

## 📌 개요

Skill Router v1 의 점진적 도입을 위한 단계별 로드맵입니다. 각 Phase 는 명확한 산출물과 성공 기준을 가지며, 이전 Phase 의 결과를 기반으로 다음 단계로 진행됩니다.

**주요 변화 (v1 → v2):**
- ✨ **Installation Automation** 단계 추가
- 📊 **Health Metrics** 수집 및 연동 단계 분리
- 🎯 **Golden Tasks** 평가 프레임워크 조기 도입
- 🔄 **Shadow Mode** A/B 테스트 기간 확대
- 🚀 **Phase 5** 추가: Advanced Features

---

## 🎯 Phase 0 (Week 1) — Inventory & Metadata Enhancement

### 목표
전체 스킬 인벤토리 확보 및 v2 메타데이터 템플릿 적용

### 작업 항목

#### 1. **Skill Inventory Scan**
```bash
# 전체 스킬 목록 추출
find skills/ -name "SKILL.md" -o -name "*.json" | wc -l

# 메타 필드 자동 추출 스크립트
./scripts/extract-skill-metadata.sh > output/skill_inventory.json
```

**산출물:**
- `data/skill_inventory.json` (전체 스킬 목록)
- `data/skill_metadata_raw.json` (추출된 메타데이터)

#### 2. **Metadata Template Enforcement**
- v2 Schema 준수 여부 검증 스크립트 작성
- 누락 필드 자동 보정 로직 구현
- Install metadata 템플릿 생성

**예시:**
```json
// templates/install-template.json
{
  "install": [
    {
      "id": "brew-example",
      "kind": "brew",
      "formula": "PACKAGE_NAME",
      "bins": ["command-name"],
      "label": "Install PACKAGE_NAME (brew)",
      "required": true
    }
  ],
  "environment_checks": [
    {
      "command": "command-name --version",
      "error_message": "Package not installed. Run 'brew install PACKAGE_NAME'.",
      "fallback_suggestion": "Use alternative skill or install required package."
    }
  ]
}
```

#### 3. **Conflict & Duplicate Detection**
```typescript
// 자동 감지 로직
const conflicts = detectConflicts(allSkills);
const duplicates = findDuplicates(allSkills);
const deprecated = listDeprecatedSkills(allSkills);
```

**산출물:**
- `data/conflicts_report.json`
- `data/duplicates_report.json`
- `data/deprecated_candidates.json`

#### 4. **Golden Task Definition**
- 초기 30 개 Golden Task 정의
- 각 Task 에 기대되는 Top-1~3 스킬 명시
- 테스트 케이스 구조 설계

**산출물:**
- `tests/golden-tasks/golden-tasks-001.jsonl` (30 개 Task)

### ✅ Success Criteria
- [ ] 전체 스킬 100% 인벤토리 완료
- [ ] 필수 메타 필드 100% 채움
- [ ] Install metadata 80% 이상 적용 (의존성 있는 스킬 기준)
- [ ] Golden Task 30 개 정의 완료
- [ ] 충돌/중복 목록화 완료

### ⚠️ Risks & Mitigations
| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| 메타 누락 스킬 많음 | 높음 | 자동 보정 스크립트 우선 구현 |
| Golden Task 편향 | 중 | 다수 기여자에게 리뷰 요청 |
| 스킬 설명 부재 | 중 | LLM 기반 자동 설명 생성 |

---

## 🎯 Phase 1 (Week 2-3) — Filter Router + Dependency Check

### 목표
Stage A 필터 구현 및 의존성 자동화 파이프라인 구축

### 작업 항목

#### 1. **Stage A Filter Implementation**
```typescript
// src/router/stage-a-filter.ts
export async function stageAFilter(
  context: RouterContext,
  registry: SkillRegistry
): Promise<SkillCandidate[]> {
  const candidates = await applyFilters(registry, [
    statusFilter,           // active 만
    installCheck,           // 의존성 확인
    toolAvailability,       // 도구 가용성
    riskGuardrail,          // 승인 확인
    conflictCheck,          // 충돌 확인
    contextAwareFilter      // 채널/권한 확인
  ], context);
  
  return candidates;
}
```

**필터별 구현:**
- ✅ Status Filter: `active` 만 통과
- ✅ Install Check: `install[]` 검증 + `environment_checks` 실행
- ✅ Tool Availability: `required_tools` 가용성 확인
- ✅ Risk Guardrail: `high risk` 승인 확인
- ✅ Conflict Check: `conflicts[]` 중복 확인
- ✅ Context-Aware: `available_in[]` 채널/권한 확인

#### 2. **Dependency Installation Automation**
```typescript
// src/dependency/install-manager.ts
export class InstallManager {
  async install(skill: Skill, context: InstallContext): Promise<InstallResult> {
    for (const install of skill.install) {
      if (install.required && !this.isInstalled(install)) {
        const result = await this.executeInstall(install);
        if (!result.success) {
          return { success: false, error: result.error };
        }
      }
    }
    return { success: true };
  }
  
  async verify(skill: Skill): Promise<VerifyResult> {
    const results = await Promise.all(
      skill.environment_checks.map(check => this.executeCheck(check))
    );
    
    const failed = results.filter(r => !r.success);
    return {
      success: failed.length === 0,
      failures: failed
    };
  }
}
```

**산출물:**
- `src/dependency/install-manager.ts`
- `src/dependency/environment-verifier.ts`
- `src/dependency/package-managers.ts` (brew, apt, npm, pip 등)

#### 3. **Shadow Mode Implementation**
```typescript
// shadow comparison logic
const shadowResult = await runShadowMode({
  context,
  legacySelected: legacyRouter.select(context),
  routerSelected: newRouter.select(context)
});

// 로그 기록
logger.info('Shadow comparison', {
  runId: shadowResult.runId,
  agreement: shadowResult.agreement,
  agreementRate: shadowResult.agreementRate,
  divergenceReason: shadowResult.divergenceReason
});
```

#### 4. **A/B Comparison Dashboard**
- Shadow 모드 결과 대시보드
- Top-1 일치율 추이 그래프
- 차이버 사유 분석 차트

**산출물:**
- `metrics/shadow-comparison-dashboard.html`

### ✅ Success Criteria
- [ ] Stage A 필터 100% 구현
- [ ] Install 자동화 80% 이상 완료
- [ ] Environment verification 100% 동작
- [ ] Shadow 모드 정상 작동
- [ ] A/B 대시보드 제공
- [ ] Stage A latency < 100ms (P50)

### ⚠️ Risks & Mitigations
| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| 설치 실패율 높음 | 높음 | 수동 설치 가이드 자동 생성 |
| Shadow 모드 오버헤드 | 중 | 샘플링 전략 도입 |
| 채널 정책 오버스펙트 | 중 | whitelist 기반 점진적 확장 |

---

## 🎯 Phase 2 (Week 4-5) — Rank Router + Health Metrics

### 목표
Stage B 점수식 랭킹 구현 및 실시간 Health Metrics 연동

### 작업 항목

#### 1. **Stage B Ranking Implementation**
```typescript
// src/router/stage-b-ranker.ts
export async function stageBRank(
  context: RouterContext,
  candidates: SkillCandidate[]
): Promise<RankedSkill[]> {
  return Promise.all(candidates.map(async (candidate) => {
    const skill = await getSkillById(candidate.skillId);
    
    const score = {
      intentMatch: scoreIntentMatch(context.intent, skill),
      vectorSimilarity: scoreVectorSimilarity(context.intent, skill),
      qualityScore: skill.quality_score,
      policyFit: scorePolicyFit(skill, context),
      latencyFit: scoreLatencyFit(skill, context),
      costFit: scoreCostFit(skill, context),
      modelFit: scoreModelFit(skill, context.currentModel),
      contextBonus: scoreContextBonus(skill, context),
      healthPenalty: calculateHealthPenalty(skill),
      penalties: calculatePenalties(skill, context)
    };
    
    const total = calculateTotalScore(score, WEIGHTS);
    
    return {
      ...candidate,
      score: total,
      scoreBreakdown: score,
      selectionReason: generateReason(skill, score)
    };
  }));
}
```

#### 2. **Health Metrics Collection Pipeline**
```typescript
// src/metrics/health-collector.ts
export class HealthMetricsCollector {
  async collect(skillId: string): Promise<RuntimeMetrics> {
    const executions = await getRecentExecutions(skillId, { days: 7 });
    
    return {
      success_rate_7d: this.calculateSuccessRate(executions, 7),
      success_rate_30d: this.calculateSuccessRate(executions, 30),
      avg_latency_ms: this.calculateAvgLatency(executions),
      p95_latency_ms: this.calculatePercentileLatency(executions, 0.95),
      p99_latency_ms: this.calculatePercentileLatency(executions, 0.99),
      error_rate_7d: this.calculateErrorRate(executions, 7),
      usage_count_7d: executions.length,
      last_failure_at: this.getLastFailureTime(executions),
      failure_class: this.getLastFailureClass(executions),
      consecutive_failures: this.getConsecutiveFailures(executions),
      last_updated: new Date().toISOString(),
      sample_size: executions.length
    };
  }
  
  async updateAllSkills(): Promise<void> {
    const skills = await getAllSkills();
    await Promise.all(
      skills.map(skill => this.collectAndStore(skill.skill_id))
    );
  }
}
```

#### 3. **Dynamic Scoring Tuning**
- 가중치 자동 조정 알고리즘
- 실패 패턴 기반 패널티 조정
- A/B 테스트 결과 반영

#### 4. **Model Fit Optimization**
```typescript
// 모델별 추천 스킬 매핑
const modelSkillMapping = {
  'anthropic/claude-3.5-sonnet': {
    strengths: ['code', 'debug', 'creative'],
    recommendedSkills: ['github', 'coding-agent', 'summarize']
  },
  'openai/gpt-4o': {
    strengths: ['writing', 'analytics'],
    recommendedSkills: ['summarize', 'research', 'analysis']
  }
};
```

**산출물:**
- `src/metrics/health-collector.ts`
- `src/metrics/health-dashboard.html`
- `src/router/stage-b-ranker.ts`
- `src/utils/scoring-tuner.ts`

### ✅ Success Criteria
- [ ] Stage B 점수식 100% 구현
- [ ] Health Metrics 수집 파이프라인 정상 작동
- [ ] Model Fit 로직 동작
- [ ] 선택 근거 로그 100% 생성
- [ ] Stage B latency < 200ms (P50)
- [ ] Total latency < 300ms (P50)

### ⚠️ Risks & Mitigations
| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| 메트릭 수집 오버헤드 | 중 | 비동기 배치 처리 |
| 가중치 편향 | 중 | 다중 메트릭 교차 검증 |
| 모델 매칭 부정확 | 중 | 수동 튜닝 + 자동 조정 병행 |

---

## 🎯 Phase 3 (Week 6) — Policy & Guardrails

### 목표
정책 엔진 완성 및 고위험 행동 승인 게이트 구현

### 작업 항목

#### 1. **Enhanced Approval Flow**
```typescript
// src/policy/approval-workflow.ts
export class ApprovalWorkflow {
  async requestApproval(
    skillId: string, 
    requester: string
  ): Promise<ApprovalRequest> {
    const request: ApprovalRequest = {
      requestId: uuidv4(),
      skillId,
      requester,
      riskReason: await this.getRiskReason(skillId),
      status: 'pending',
      requestedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
      approvers: await this.getApprovers(skillId)
    };
    
    await this.storeApprovalRequest(request);
    await this.sendNotifications(request.approvers, request);
    
    return request;
  }
  
  async approve(requestId: string, approver: string): Promise<boolean> {
    const request = await this.getApprovalRequest(requestId);
    
    if (!request) throw new Error('Request not found');
    if (request.status !== 'pending') throw new Error('Already processed');
    if (new Date() > new Date(request.expiresAt)) {
      throw new Error('Request expired');
    }
    
    request.status = 'approved';
    request.approvedBy = approver;
    request.approvedAt = new Date().toISOString();
    request.token = this.generateApprovalToken(requestId);
    
    await this.storeApprovalRequest(request);
    
    return true;
  }
}
```

#### 2. **Channel-Level Policy Engine**
```typescript
// src/policy/channel-policy.ts
export class ChannelPolicyEngine {
  checkSkillAvailability(
    skill: Skill,
    channel: ChannelInfo
  ): PolicyDecision {
    const { channels, group_policy, dm_policy } = skill.available_in || {};
    
    // 채널 가용성 확인
    if (channels && !channels.includes(channel.type)) {
      return { allowed: false, reason: 'Channel not supported' };
    }
    
    // 그룹 채널 정책
    if (channel.isGroup) {
      if (group_policy === 'deny') {
        return { allowed: false, reason: 'Blocked in groups' };
      }
      if (group_policy === 'require_mention' && !channel.isUserMention) {
        return { allowed: false, reason: 'Requires mention' };
      }
    }
    
    // DM 정책
    if (!channel.isGroup && dm_policy === 'deny') {
      return { allowed: false, reason: 'Blocked in DMs' };
    }
    
    return { allowed: true };
  }
}
```

#### 3. **Restricted Actions Gate**
```typescript
const RESTRICTED_ACTIONS = [
  'external_send',
  'destructive',
  'financial_transfer',
  'mass_update',
  'admin_operations'
];

function checkRestrictedActions(skill: Skill): PolicyDecision {
  const actions = skill.capabilities || [];
  const restricted = actions.filter(a => RESTRICTED_ACTIONS.includes(a));
  
  if (restricted.length > 0) {
    return {
      allowed: false,
      requiresApproval: true,
      restrictedActions: restricted,
      approvalLevel: 'high' // admin-level approval needed
    };
  }
  
  return { allowed: true };
}
```

#### 4. **Policy Monitoring Dashboard**
- 정책 차단 이벤트 실시간 모니터링
- 승인 요청 상태 추적
- 정책 위반 이력 감사 로그

**산출물:**
- `src/policy/approval-workflow.ts`
- `src/policy/channel-policy.ts`
- `src/policy/restricted-actions-gate.ts`
- `metrics/policy-dashboard.html`

### ✅ Success Criteria
- [ ] 승인 워크플로우 100% 구현
- [ ] Channel-level 정책 100% 동작
- [ ] Restricted actions gate 정상 작동
- [ ] 정책 대시보드 제공
- [ ] 승인 처리 시간 < 5 분 (평균)
- [ ] Policy violation leakage = 0

### ⚠️ Risks & Mitigations
| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| 승인 지연 | 높음 | 타임아웃 자동 거절 + 알림 강화 |
| 정책 오버스펙트 | 중 | whitelist 기반 점진적 적용 |
| 감사 로그 누락 | 중 | 이중 기록 + 정기 감사 |

---

## 🎯 Phase 4 (Ongoing) — Eval & Feedback Loop

### 목표
지속적인 품질 개선 및 자동 튜닝 파이프라인 운영

### 작업 항목

#### 1. **Golden Task Evaluation Framework**
```typescript
// tests/golden-tasks/eval-runner.ts
export async function runGoldenTaskEvaluation(): Promise<EvaluationResult> {
  const tasks = await loadGoldenTasks('tests/golden-tasks/*.jsonl');
  
  const results = await Promise.all(tasks.map(async (task) => {
    const routerResult = await router.select(task.context);
    const selected = routerResult.selected.map(s => s.skillId);
    
    return {
      taskId: task.id,
      expected: task.expectedSkills,
      actual: selected,
      top1Match: selected[0] === task.expectedSkills[0],
      top3Match: selected.some(s => task.expectedSkills.includes(s)),
      precision: calculatePrecision(selected, task.expectedSkills),
      recall: calculateRecall(selected, task.expectedSkills),
      latency: routerResult.stageLatencyMs.total
    };
  }));
  
  return {
    totalTasks: tasks.length,
    top1Accuracy: results.filter(r => r.top1Match).length / tasks.length,
    top3Recall: results.filter(r => r.top3Match).length / tasks.length,
    avgPrecision: results.reduce((a, b) => a + b.precision, 0) / tasks.length,
    avgRecall: results.reduce((a, b) => a + b.recall, 0) / tasks.length,
    avgLatency: results.reduce((a, b) => a + b.latency, 0) / tasks.length
  };
}
```

#### 2. **Weekly Tuning Cycle**
```bash
# 주간 자동 튜닝 스케줄 (cron)
0 0 * * 1 /usr/local/bin/weekly-tuning.sh

# 스크립트 내용
#!/bin/bash
# 1. Golden Task 실행
./scripts/run-golden-tasks.sh > output/weekly-eval.json

# 2. 가중치 분석
./scripts/analyze-weights.py output/weekly-eval.json > output/weight-adjustments.json

# 3. 정책 검토
./scripts/review-policies.py > output/policy-recommendations.json

# 4. 리포트 생성
./scripts/generate-weekly-report.sh output/ > reports/weekly-YYYY-MM-DD.md
```

#### 3. **Health Metrics Monitoring**
```typescript
// 실시간 메트릭 대시보드
const dashboard = {
  success_rate_7d: {
    overall: 0.92,
    trending: 'stable',
    alertThreshold: 0.85
  },
  avg_latency_ms: {
    overall: 245,
    p95: 480,
    p99: 720,
    alertThreshold: 1200
  },
  install_success_rate: {
    overall: 0.96,
    trending: 'improving',
    alertThreshold: 0.90
  },
  shadow_agreement_rate: {
    overall: 0.85,
    trending: 'stable',
    alertThreshold: 0.80
  }
};
```

#### 4. **Skill Deprecation Pipeline**
```typescript
// 저성과 스킬 자동 식별
function identifyLowPerformingSkills(skills: Skill[]): DeprecationCandidate[] {
  return skills
    .filter(skill => {
      const metrics = skill.metrics;
      if (!metrics) return false;
      
      // 실패율 > 20%
      if (metrics.error_rate_7d > 0.20) return true;
      
      // 사용량 거의 없음 (30 일 < 5 회)
      if (metrics.usage_count_30d < 5) return true;
      
      // 연속 실패 >= 3 회
      if (metrics.consecutive_failures >= 3) return true;
      
      return false;
    })
    .map(skill => ({
      skillId: skill.skill_id,
      reason: identifyDeprecationReason(skill.metrics),
      replacement: skill.compatibility?.replaced_by,
      recommendedAction: 'deprecate'
    }));
}
```

**산출물:**
- `scripts/weekly-tuning.sh`
- `scripts/run-golden-tasks.sh`
- `scripts/analyze-weights.py`
- `reports/weekly-YYYY-MM-DD.md`
- `metrics/live-dashboard.html`

### ✅ Success Criteria (Ongoing)
- [ ] 주간 Golden Task 평가 자동 실행
- [ ] Top-1 정확도 >= 85% 유지
- [ ] Average latency < 300ms (P50) 유지
- [ ] Install success rate >= 95% 유지
- [ ] Shadow agreement rate >= 80% 유지
- [ ] 주간 리포트 자동 생성

### ⚠️ Risks & Mitigations
| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| 메트릭 편향 | 중 | 다중 지표 교차 검증 |
| 자동 튜닝 오버피팅 | 중 | 수동 검토 단계 유지 |
| 저성과 스킬 제거 저항 | 중 | 단계적 deprecation + 대체 스킬 제공 |

---

## 🚀 Phase 5 (Week 7-9) — Advanced Features (Optional)

### 목표
고급 기능 구현 및 차별화된 라우팅 경험 제공

### 작업 항목

#### 1. **Context-Aware Skill Pruning**
- 세션별/채널별 동적 스킬 필터링
- 사용자 선호도 학습 및 적용
- 컨텍스트 히스토리 기반 추천

#### 2. **Version Management & Rollback**
- 스킬 버전 호환성 관리
- 자동 롤백 트리거 (실패율 급증 시)
- 점진적 rollout (canary deployment)

#### 3. **Multi-Model Fallback**
- 모델별 스킬 매칭 최적화
- 모델 실패 시 자동 전환
- 비용/성능 최적화 라우팅

#### 4. **User Preference Customization**
- 사용자별 선호도 저장
- "이 스킬 쓰지 마" 블록 리스트
- "항상 이 모델로" 선호 설정

**산출물:**
- `src/context/context-aware-router.ts`
- `src/versioning/version-manager.ts`
- `src/model/model-fallback.ts`
- `src/preferences/user-preference-store.ts`

### ✅ Success Criteria
- [ ] 컨텍스트-aware 라우팅 80% 이상 커버리지
- [ ] 롤백 시간 < 1 분
- [ ] Multi-model fallback 정상 작동
- [ ] 사용자 선호도 저장/적용 100%

---

## 📊 전체 진행 현황

| Phase | 목표 기간 | 진행도 | 주요 산출물 |
|-------|-----------|--------|-------------|
| **Phase 0** | Week 1 | TODO | 스킬 인벤토리, 메타데이터, Golden Tasks |
| **Phase 1** | Week 2-3 | TODO | Stage A 필터, Install 자동화, Shadow 모드 |
| **Phase 2** | Week 4-5 | TODO | Stage B 랭킹, Health Metrics, Model Fit |
| **Phase 3** | Week 6 | TODO | 승인 워크플로우, Channel 정책, 감사 로그 |
| **Phase 4** | Ongoing | TODO | 평가 프레임워크, 자동 튜닝, 주간 리포트 |
| **Phase 5** | Week 7-9 | TODO | 컨텍스트-aware, 버전 관리, Multi-model |

---

## 🎯 최종 성공 지표 (SLO)

| 지표 | 목표 | 측정 주기 |
|------|------|-----------|
| P50 Routing Latency | < 300ms | 실시간 |
| P95 Routing Latency | < 1200ms | 실시간 |
| Top-1 Precision | >= 85% | 주간 |
| Top-3 Recall | >= 90% | 주간 |
| Shadow Agreement Rate | >= 80% | 일간 |
| Install Success Rate | >= 95% | 실시간 |
| Policy Violation Leakage | = 0 | 실시간 |
| Recovery Rate (reroute) | >= 70% | 주간 |

---

## 📚 참조 문서

- [SKILL_ROUTER_V1_PLAN.md](SKILL_ROUTER_V1_PLAN.md)
- [SKILL_REGISTRY_SCHEMA.md](SKILL_REGISTRY_SCHEMA.md)
- [ROUTING_POLICY.md](ROUTING_POLICY.md)
- [ROUTER_API_SPEC.md](ROUTER_API_SPEC.md)
- [OpenClaw Documentation](https://docs.openclaw.ai)

---

## 📝 Changelog

### v2.0.0 (2026-03-05)
- ✨ Installation Automation 단계 추가
- 📊 Health Metrics 수집 파이프라인 분리
- 🎯 Golden Tasks 조기 도입
- 🔄 Shadow Mode 기간 확대
- 🚀 Phase 5 (Advanced Features) 추가
- 📊 전체 진행 현황 대시보드

### v1.0.0 (2026-03-05)
- 초기 로드맵 정의
- 4 단계 기본 계획
```
</think>

다음은 `PHASE_ROADMAP.md` 의 새로운 v2 버전입니다:

```markdown
# Phase Roadmap (v2)

**작성일:** 2026-03-05  
**최종 업데이트:** 2026-03-05 (OpenClaw 벤치마킹 반영)  
**버전:** 2.0

---

## 📌 개요

Skill Router v1 의 점진적 도입을 위한 단계별 로드맵입니다. 각 Phase 는 명확한 산출물과 성공 기준을 가지며, 이전 Phase 의 결과를 기반으로 다음 단계로 진행됩니다.

**주요 변화 (v1 → v2):**
- ✨ **Installation Automation** 단계 추가
- 📊 **Health Metrics** 수집 및 연동 단계 분리
- 🎯 **Golden Tasks** 평가 프레임워크 조기 도입
- 🔄 **Shadow Mode** A/B 테스트 기간 확대
- 🚀 **Phase 5** 추가: Advanced Features

---

## 🎯 Phase 0 (Week 1) — Inventory & Metadata Enhancement

### 목표
전체 스킬 인벤토리 확보 및 v2 메타데이터 템플릿 적용

### 작업 항목

#### 1. **Skill Inventory Scan**
```bash
# 전체 스킬 목록 추출
find skills/ -name "SKILL.md" -o -name "*.json" | wc -l

# 메타 필드 자동 추출 스크립트
./scripts/extract-skill-metadata.sh > output/skill_inventory.json
```

**산출물:**
- `data/skill_inventory.json` (전체 스킬 목록)
- `data/skill_metadata_raw.json` (추출된 메타데이터)

#### 2. **Metadata Template Enforcement**
- v2 Schema 준수 여부 검증 스크립트 작성
- 누락 필드 자동 보정 로직 구현
- Install metadata 템플릿 생성

#### 3. **Conflict & Duplicate Detection**
```typescript
// 자동 감지 로직
const conflicts = detectConflicts(allSkills);
const duplicates = findDuplicates(allSkills);
const deprecated = listDeprecatedSkills(allSkills);
```

**산출물:**
- `data/conflicts_report.json`
- `data/duplicates_report.json`
- `data/deprecated_candidates.json`

#### 4. **Golden Task Definition**
- 초기 30 개 Golden Task 정의
- 각 Task 에 기대되는 Top-1~3 스킬 명시
- 테스트 케이스 구조 설계

**산출물:**
- `tests/golden-tasks/golden-tasks-001.jsonl` (30 개 Task)

### ✅ Success Criteria
- [ ] 전체 스킬 100% 인벤토리 완료
- [ ] 필수 메타 필드 100% 채움
- [ ] Install metadata 80% 이상 적용 (의존성 있는 스킬 기준)
- [ ] Golden Task 30 개 정의 완료
- [ ] 충돌/중복 목록화 완료

### ⚠️ Risks & Mitigations
| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| 메타 누락 스킬 많음 | 높음 | 자동 보정 스크립트 우선 구현 |
| Golden Task 편향 | 중 | 다수 기여자에게 리뷰 요청 |
| 스킬 설명 부재 | 중 | LLM 기반 자동 설명 생성 |

---

## 🎯 Phase 1 (Week 2-3) — Filter Router + Dependency Check

### 목표
Stage A 필터 구현 및 의존성 자동화 파이프라인 구축

### 작업 항목

#### 1. **Stage A Filter Implementation**
```typescript
// src/router/stage-a-filter.ts
export async function stageAFilter(
  context: RouterContext,
  registry: SkillRegistry
): Promise<SkillCandidate[]> {
  const candidates = await applyFilters(registry, [
    statusFilter,           // active 만
    installCheck,           // 의존성 확인
    toolAvailability,       // 도구 가용성
    riskGuardrail,          // 승인 확인
    conflictCheck,          // 충돌 확인
    contextAwareFilter      // 채널/권한 확인
  ], context);
  
  return candidates;
}
```

**필터별 구현:**
- ✅ Status Filter: `active` 만 통과
- ✅ Install Check: `install[]` 검증 + `environment_checks` 실행
- ✅ Tool Availability: `required_tools` 가용성 확인
- ✅ Risk Guardrail: `high risk` 승인 확인
- ✅ Conflict Check: `conflicts[]` 중복 확인
- ✅ Context-Aware: `available_in[]` 채널/권한 확인

#### 2. **Dependency Installation Automation**
```typescript
// src/dependency/install-manager.ts
export class InstallManager {
  async install(skill: Skill, context: InstallContext): Promise<InstallResult> {
    for (const install of skill.install) {
      if (install.required && !this.isInstalled(install)) {
        const result = await this.executeInstall(install);
        if (!result.success) {
          return { success: false, error: result.error };
        }
      }
    }
    return { success: true };
  }
  
  async verify(skill: Skill): Promise<VerifyResult> {
    const results = await Promise.all(
      skill.environment_checks.map(check => this.executeCheck(check))
    );
    
    const failed = results.filter(r => !r.success);
    return {
      success: failed.length === 0,
      failures: failed
    };
  }
}
```

**산출물:**
- `src/dependency/install-manager.ts`
- `src/dependency/environment-verifier.ts`
- `src/dependency/package-managers.ts` (brew, apt, npm, pip 등)

#### 3. **Shadow Mode Implementation**
```typescript
// shadow comparison logic
const shadowResult = await runShadowMode({
  context,
  legacySelected: legacyRouter.select(context),
  routerSelected: newRouter.select(context)
});

// 로그 기록
logger.info('Shadow comparison', {
  runId: shadowResult.runId,
  agreement: shadowResult.agreement,
  agreementRate: shadowResult.agreementRate,
  divergenceReason: shadowResult.divergenceReason
});
```

#### 4. **A/B Comparison Dashboard**
- Shadow 모드 결과 대시보드
- Top-1 일치율 추이 그래프
- 차이버 사유 분석 차트

**산출물:**
- `metrics/shadow-comparison-dashboard.html`

### ✅ Success Criteria
- [ ] Stage A 필터 100% 구현
- [ ] Install 자동화 80% 이상 완료
- [ ] Environment verification 100% 동작
- [ ] Shadow 모드 정상 작동
- [ ] A/B 대시보드 제공
- [ ] Stage A latency < 100ms (P50)

### ⚠️ Risks & Mitigations
| 리스크 | 영향도 | 대응책 |
|--------|--------|--------|
| 설치 실패율 높음 | 높음 | 수동 설치 가이드 자동 생성 |
| Shadow 모드 오버헤드 | 중 | 샘플링 전략 도입 |
| 채널 정책 오버스펙트 | 중 | whitelist 기반 점진적 확장 |

---

## 🎯 Phase 2 (Week 4-5) — Rank Router + Health Metrics

### 목표
Stage B 점수식 랭킹 구현 및 실시간 Health Metrics 연동

### 작업 항목

#### 1. **Stage B Ranking Implementation**
```typescript
// src/router/stage-b-ranker.ts
export async function stageBRank(
  context: RouterContext,
  candidates: SkillCandidate[]
): Promise<RankedSkill[]> {
  return Promise.all(candidates.map(async (candidate) => {
    const skill = await getSkillById(candidate.skillId);
    
    const score = {
      intentMatch: scoreIntentMatch(context.intent, skill),
      vectorSimilarity: scoreVectorSimilarity(context.intent, skill),
      qualityScore: skill.quality_score,
      policyFit: scorePolicyFit(skill, context),
      latencyFit: scoreLatencyFit(skill, context),
      costFit: scoreCostFit(skill, context),
      modelFit: scoreModelFit(skill, context.currentModel),
      contextBonus: scoreContextBonus(skill, context),
      healthPenalty: calculateHealthPenalty(skill),
      penalties: calculatePenalties(skill, context)
    };
    
    const total = calculateTotalScore(score, WEIGHTS);
    
    return {
      ...candidate,
      score: total,
      scoreBreakdown: score,
      selectionReason: generateReason(skill, score)
    };
  }));
}
```

#### 2. **Health Metrics Collection Pipeline**
```typescript
// src/metrics/health-collector.ts
export class HealthMetricsCollector {
  async collect(skillId: string): Promise<RuntimeMetrics> {
    const executions = await getRecentExecutions(skillId, { days: 7 });
    
    return {
      success_rate_7d: this.calculateSuccessRate(executions, 7),
      success_rate_30d: this.calculateSuccessRate(executions, 30),
      avg_latency_ms: this.calculateAvgLatency(executions),
      p95_latency_ms: this.calculatePercentileLatency(executions, 0.95),
      p99_latency_ms: this.calculatePercentileLatency(executions, 0.99),
      error_rate_7d: this.calculateErrorRate(executions, 7),
      usage_count_7d: executions.length,
      last_failure_at: this.getLastFailureTime(executions),
      failure_class: this.getLastFailureClass(executions),
      consecutive_failures: this.getConsecutiveFailures(executions),
      last_updated: new Date().toISOString(),
      sample_size: