# Skill Registry Schema (v2)

작성일: 2026-03-05
업데이트: 2026-03-05 (OpenClaw 벤치마킹 반영)

---

## 📌 개요

Skill Registry Schema v2 는 스킬 라우팅, 의존성 관리, 실시간 모니터링, 컨텍스트 인식 라우팅을 지원하기 위해 확장되었습니다.

**주요 변화:**
- ✨ Installation & Dependency 자동화 필드 추가 (OpenClaw 벤치마킹)
- 📊 Runtime Metrics 실시간 수집 필드 추가
- 🔗 Versioning & Compatibility 관리 필드 추가
- 🎯 Context-Aware 라우팅 필드 추가
- 🤖 Model Fit 최적화 필드 추가

---

## ✅ Required Fields (필수 필드)

모든 스킬은 다음 필드를 반드시 가져야 합니다.

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `skill_id` | string | 고유 스킬 식별자 (kebab-case) | `github`, `systematic-debugging` |
| `version` | string | Semver 버전 | `1.0.0`, `2.1.0` |
| `status` | enum | 스킬 상태 | `active` \| `deprecated` \| `experimental` |
| `domain` | string | 도메인 분류 | `engineering` \| `devops` \| `productivity` |
| `intents` | string[] | 처리 가능한 의도 목록 | `["debug", "create-pr"]` |
| `risk_level` | enum | 위험 수준 | `low` \| `medium` \| `high` |
| `required_tools` | string[] | 필요 도구 목록 | `["exec", "read", "gh"]` |
| `latency_class` | enum | 지연 클래스 | `fast` \| `normal` \| `slow` |
| `cost_class` | enum | 비용 클래스 | `low` \| `normal` \| `high` |
| `conflicts` | string[] | 충돌하는 스킬 목록 | `["legacy-debugger"]` |
| `dependencies` | string[] | 의존하는 다른 스킬 | `["file-reader"]` |
| `quality_score` | number | 품질 점수 (0.0~1.0) | `0.88` |

---

## 🆕 Installation & Dependency (OpenClaw 벤치마킹)

스킬 실행 전 의존성 설치 및 검증을 위한 필드입니다.

### `install[]` (Installation Options)

```typescript
interface InstallOption {
  id: string;              // 고유 설치 식별자
  kind: string;            // 설치 방식: brew/apt/npm/pip/dnf/choco/snap/...
  formula?: string;        // brew package 이름
  package?: string;        // apt/npm 패키지 이름
  bins?: string[];         // 설치 후 생성되는 바이너리 목록
  label: string;           // 사용자에게 표시되는 설치 레이블
  required: boolean;       // 필수 여부 (true 면 스킬 사용 불가)
  version?: string;        // 특정 버전 요구사항
}
```

**예시:**
```json
"install": [
  {
    "id": "brew-gh",
    "kind": "brew",
    "formula": "gh",
    "bins": ["gh"],
    "label": "Install GitHub CLI (brew)",
    "required": true
  },
  {
    "id": "npm-some-cli",
    "kind": "npm",
    "package": "some-global-cli",
    "global": true,
    "bins": ["some-cmd"],
    "label": "Install some-cli (npm global)",
    "required": false
  }
]
```

### `environment_checks[]` (환경 검증)

```typescript
interface EnvironmentCheck {
  command: string;         // 검증용 명령어
  error_message: string;   // 실패 시 표시 메시지
  fallback_suggestion?: string;  // 대체 방안 제안
  timeout_ms?: number;     // 명령어 실행 타임아웃 (기본 5000)
}
```

**예시:**
```json
"environment_checks": [
  {
    "command": "gh --version",
    "error_message": "GitHub CLI not installed. Run 'brew install gh'.",
    "fallback_suggestion": "Use browser tool instead for GitHub operations.",
    "timeout_ms": 3000
  }
]
```

### `install_policy` (설치 정책)

```typescript
type InstallPolicy = 'auto' | 'confirm' | 'deny';
```

- `auto`: 의존성 자동 설치 (안전한 도구만)
- `confirm`: 설치 전 사용자에게 확인
- `deny`: 자동 설치 금지 (수동 설치 요구)

---

## 📊 Runtime Metrics (실시간 메트릭)

실행 시간 동안 동적으로 업데이트되는 성능 지표입니다.

```typescript
interface RuntimeMetrics {
  // 성능 지표
  success_rate_7d: number;        // 7 일 성공률 (0.0~1.0)
  success_rate_30d: number;       // 30 일 성공률 (0.0~1.0)
  avg_latency_ms: number;         // 평균 지연 시간 (ms)
  p95_latency_ms: number;         // P95 지연 시간 (ms)
  p99_latency_ms: number;         // P99 지연 시간 (ms)
  error_rate_7d: number;          // 7 일 오류율 (0.0~1.0)
  
  // 사용량 지표
  usage_count_7d: number;         // 7 일 사용 횟수
  usage_count_30d: number;        // 30 일 사용 횟수
  avg_tokens_per_call: number;    // 평균 토큰 사용량
  
  // 실패 정보
  last_failure_at?: string;       // 마지막 실패 시간 (ISO 8601)
  failure_class?: string;         // 마지막 실패 분류
  consecutive_failures: number;   // 연속 실패 횟수
  
  // 업데이트 정보
  last_updated: string;           // 메트릭 최종 업데이트 시간 (ISO 8601)
  sample_size: number;            // 통계 기반 샘플 수
}
```

**예시:**
```json
"metrics": {
  "success_rate_7d": 0.94,
  "success_rate_30d": 0.91,
  "avg_latency_ms": 245,
  "p95_latency_ms": 480,
  "p99_latency_ms": 720,
  "error_rate_7d": 0.06,
  "usage_count_7d": 156,
  "usage_count_30d": 542,
  "avg_tokens_per_call": 1250,
  "last_failure_at": "2026-03-04T15:30:00Z",
  "failure_class": "tool_unavailable",
  "consecutive_failures": 0,
  "last_updated": "2026-03-05T10:00:00Z",
  "sample_size": 542
}
```

---

## 🔗 Versioning & Compatibility

버전 관리 및 호환성 정보입니다.

```typescript
interface VersionCompatibility {
  min_router_version: string;    // 요구하는 최소 라우터 버전 (Semver)
  deprecated_in?: string;         // deprecation 된 버전
  deprecated_at?: string;         // deprecation 시간 (ISO 8601)
  replaced_by?: string;           // 대체 스킬 ID
  migration_guide?: string;       // 마이그레이션 가이드 URL
  
  // Breaking changes 정보
  breaking_changes?: string[];    // 이 버전의 Breaking Changes 목록
}
```

```typescript
interface ChangelogEntry {
  version: string;
  date: string;                   // ISO 8601
  changes: string[];              // 변경 사항 목록
  breaking?: boolean;             // Breaking Change 여부
}
```

**예시:**
```json
"compatibility": {
  "min_router_version": "1.0.0",
  "deprecated_in": "2.2.0",
  "replaced_by": "github-advanced"
},
"changelog": [
  {
    "version": "2.1.0",
    "date": "2026-03-01",
    "changes": [
      "Add PR review commands",
      "Fix rate limit handling",
      "Improve JSON output parsing"
    ],
    "breaking": false
  },
  {
    "version": "2.0.0",
    "date": "2026-02-15",
    "changes": [
      "Remove legacy API commands",
      "Require GitHub CLI v2.0+"
    ],
    "breaking": true
  }
]
```

---

## 🎯 Context Awareness

채널/세션/권한 기반 컨텍스트 인식 라우팅 필드입니다.

### `available_in[]` (사용 가능 채널)

```typescript
type ChannelType = 
  | 'slack' | 'discord' | 'whatsapp' | 'telegram'
  | 'webchat' | 'local' | 'macos' | 'ios' | 'android';

interface ChannelAvailability {
  channels: ChannelType[];        // 허용된 채널 목록
  group_policy: 'allow' | 'deny' | 'require_mention';  // 그룹 채널 정책
  dm_policy: 'allow' | 'deny' | 'require_pairing';     // DM 정책
}
```

**예시:**
```json
"available_in": {
  "channels": ["slack", "discord", "local"],
  "group_policy": "require_mention",
  "dm_policy": "allow"
}
```

### `permissions_required[]` (필요 권한)

```typescript
type PermissionType = 
  | 'exec' | 'read' | 'write' | 'edit'
  | 'network' | 'browser' | 'camera'
  | 'system_run' | 'system_notify'
  | 'destructive' | 'external_send';

interface PermissionRequirement {
  permission: PermissionType;
  risk_level: 'low' | 'medium' | 'high';
  requires_approval: boolean;    // 승인 필요 여부
}
```

**예시:**
```json
"permissions_required": [
  {
    "permission": "exec",
    "risk_level": "low",
    "requires_approval": false
  },
  {
    "permission": "system_run",
    "risk_level": "high",
    "requires_approval": true
  }
]
```

### `user_preferences[]` (사용자 선호도)

```typescript
interface UserPreference {
  preferred_domains?: string[];   // 선호 도메인 목록
  blocked_skills?: string[];      // 차단된 스킬 목록
  preferred_models?: string[];    // 선호 모델 목록
  max_cost_per_call?: number;     // 최대 비용 제한
  max_latency_ms?: number;        // 최대 지연 시간
}
```

---

## 🤖 Model Fit

모델 적합도 및 최적화 필드입니다.

### `model_strengths[]` (모델 강점)

```typescript
type ModelStrength = 
  | 'code' | 'debug' | 'creative' | 'analytics'
  | 'writing' | 'planning' | 'research'
  | 'visual' | 'math' | 'language';

interface ModelStrengths {
  strengths: ModelStrength[];     // 이 스킬의 강점 영역
  weakness?: ModelStrength[];     // 약점 영역
}
```

**예시:**
```json
"model_strengths": {
  "strengths": ["code", "debug"],
  "weakness": ["creative", "writing"]
}
```

### `preferred_models[]` (선호 모델)

```typescript
interface PreferredModel {
  model_id: string;               // 모델 ID (예: "anthropic/claude-3.5-sonnet")
  priority: number;               // 우선순위 (1 = 가장 선호)
  min_capability?: string;        // 요구하는 최소 기능 수준
}
```

**예시:**
```json
"preferred_models": [
  {
    "model_id": "anthropic/claude-3.5-sonnet",
    "priority": 1
  },
  {
    "model_id": "openai/gpt-4o",
    "priority": 2
  }
]
```

---

## 📝 Optional Fields (선택 필드)

| 필드 | 타입 | 설명 |
|------|------|------|
| `owner` | string | 스킬 소유자/작성자 |
| `description` | string | 스킬 설명 (human-readable) |
| `documentation_url` | string | 문서화 URL |
| `last_verified_at` | string | 마지막 검증 시간 (ISO 8601) |
| `deprecation_reason` | string | Deprecation 사유 |
| `tags` | string[] | 태그 목록 (검색/분류용) |
| `created_at` | string | 생성 시간 (ISO 8601) |

---

## 📋 Complete Example

```json
{
  "skill_id": "github",
  "version": "2.1.0",
  "status": "active",
  "domain": "devops",
  "intents": ["debug", "create-pr", "review-code", "check-ci"],
  "risk_level": "low",
  "required_tools": ["exec", "read"],
  "latency_class": "normal",
  "cost_class": "low",
  "conflicts": ["legacy-github-cli"],
  "dependencies": [],
  "quality_score": 0.92,
  
  "install": [
    {
      "id": "brew-gh",
      "kind": "brew",
      "formula": "gh",
      "bins": ["gh"],
      "label": "Install GitHub CLI (brew)",
      "required": true,
      "version": ">=2.0.0"
    }
  ],
  
  "environment_checks": [
    {
      "command": "gh --version",
      "error_message": "GitHub CLI not installed. Run 'brew install gh'.",
      "fallback_suggestion": "Use browser tool instead for GitHub operations.",
      "timeout_ms": 3000
    },
    {
      "command": "gh auth status",
      "error_message": "GitHub CLI not authenticated. Run 'gh auth login'.",
      "fallback_suggestion": "Authentication required for all GitHub operations."
    }
  ],
  
  "install_policy": "confirm",
  
  "metrics": {
    "success_rate_7d": 0.94,
    "success_rate_30d": 0.91,
    "avg_latency_ms": 245,
    "p95_latency_ms": 480,
    "p99_latency_ms": 720,
    "error_rate_7d": 0.06,
    "usage_count_7d": 156,
    "usage_count_30d": 542,
    "avg_tokens_per_call": 1250,
    "last_failure_at": "2026-03-04T15:30:00Z",
    "failure_class": "tool_unavailable",
    "consecutive_failures": 0,
    "last_updated": "2026-03-05T10:00:00Z",
    "sample_size": 542
  },
  
  "compatibility": {
    "min_router_version": "1.0.0",
    "deprecated_in": "2.2.0",
    "replaced_by": "github-advanced"
  },
  
  "changelog": [
    {
      "version": "2.1.0",
      "date": "2026-03-01",
      "changes": [
        "Add PR review commands",
        "Fix rate limit handling",
        "Improve JSON output parsing"
      ],
      "breaking": false
    }
  ],
  
  "available_in": {
    "channels": ["slack", "discord", "local"],
    "group_policy": "require_mention",
    "dm_policy": "allow"
  },
  
  "permissions_required": [
    {
      "permission": "exec",
      "risk_level": "low",
      "requires_approval": false
    }
  ],
  
  "model_strengths": {
    "strengths": ["code", "debug", "analytics"],
    "weakness": ["creative", "writing"]
  },
  
  "preferred_models": [
    {
      "model_id": "anthropic/claude-3.5-sonnet",
      "priority": 1
    },
    {
      "model_id": "openai/gpt-4o",
      "priority": 2
    }
  ],
  
  "owner": "openclaw-community",
  "description": "GitHub operations via `gh` CLI: issues, PRs, CI runs, code review",
  "documentation_url": "https://docs.example.com/skills/github",
  "last_verified_at": "2026-03-05T08:00:00Z",
  "tags": ["github", "devops", "ci-cd", "code-review"]
}
```

---

## 🔧 Validation Rules

### 필수 검증 규칙

1. **`skill_id`**
   - kebab-case 형식: `[a-z][a-z0-9-]*[a-z0-9]`
   - 길이: 3~64 문자
   - 고유성 보장

2. **`version`**
   - Semver 형식: `MAJOR.MINOR.PATCH`
   - 예: `1.0.0`, `2.1.3`

3. **`quality_score`**
   - 범위: `0.0 <= score <= 1.0`

4. **`install[]`**
   - 각 `id` 는 고유해야 함
   - `bins[]` 는 적어도 하나의 요소를 가져야 함 (required=true 일 경우)
   - `label` 은 사용자에게 표시되는 언어로 작성

5. **`metrics`**
   - 숫자는 음수일 수 없음
   - `success_rate` 와 `error_rate` 합계 <= 1.0
   - `sample_size` >= 1 일 때만 유효한 통계

6. **`available_in`**
   - `channels` 는 적어도 하나의 채널을 포함해야 함
   - `group_policy` 와 `dm_policy` 는 유효한 값이어야 함

---

## 📈 Migration Guide (v1 → v2)

### 필수 마이그레이션 작업

```bash
# 1. 필수 필드 추가 스크립트 (예시)
for skill in skills/*.json; do
  # install_policy 추가
  jq '.install_policy = "confirm"' "$skill" > tmp.json && mv tmp.json "$skill"
  
  # metrics 초기화
  jq '.metrics = {
    "success_rate_7d": 0.9,
    "success_rate_30d": 0.9,
    "avg_latency_ms": 300,
    "p95_latency_ms": 600,
    "p99_latency_ms": 900,
    "error_rate_7d": 0.1,
    "usage_count_7d": 0,
    "usage_count_30d": 0,
    "avg_tokens_per_call": 1000,
    "consecutive_failures": 0,
    "last_updated": "'$(date -Iseconds)'",
    "sample_size": 0
  }' "$skill" > tmp.json && mv tmp.json "$skill"
  
  # available_in 초기화
  jq '.available_in = {
    "channels": ["local"],
    "group_policy": "allow",
    "dm_policy": "allow"
  }' "$skill" > tmp.json && mv tmp.json "$skill"
done
```

### 권장 마이그레이션 작업

1. `install[]` 필드 추가 (의존성 있는 스킬)
2. `environment_checks[]` 추가 (도구 검증 필요 스킬)
3. `model_strengths` 및 `preferred_models` 추가
4. `permissions_required` 상세화
5. `changelog` 시작

---

## 🚀 Best Practices

### 1. Installation Setup

```json
// ✅ 좋은 예: 명확하고 사용자 친화적
"install": [
  {
    "id": "brew-gh",
    "kind": "brew",
    "formula": "gh",
    "bins": ["gh"],
    "label": "Install GitHub CLI (brew)",
    "required": true
  }
],
"install_policy": "confirm"

// ❌ 나쁜 예: 정보가 부족함
"install": ["gh"],
"install_policy": "auto"
```

### 2. Metrics Initialization

```json
// ✅ 좋은 예: 초기값은 보수적으로 설정
"metrics": {
  "success_rate_7d": 0.85,  // 실제 값보다 낮게
  "avg_latency_ms": 500,     // 실제 값보다 높게
  "sample_size": 0           // 데이터 없음 명시
}

// ❌ 나쁜 예: 불현실적인 값
"metrics": {
  "success_rate_7d": 1.0,
  "avg_latency_ms": 50,
  "sample_size": 0
}
```

### 3. Context Awareness

```json
// ✅ 좋은 예: 채널별 정책 명시
"available_in": {
  "channels": ["slack", "discord", "local"],
  "group_policy": "require_mention",  // 그룹에서는 멘트 필요
  "dm_policy": "allow"                 // DM 은 허용
}

// ❌ 나쁜 예: 위험한 정책
"available_in": {
  "channels": ["slack", "discord"],
  "group_policy": "allow",             // 그룹에서 모든 요청 허용 (위험)
  "dm_policy": "allow"
}
```

---

## 📚 References

- [SKILL_ROUTER_V1_PLAN.md](SKILL_ROUTER_V1_PLAN.md) - 전체 계획 문서
- [ROUTING_POLICY.md](ROUTING_POLICY.md) - 라우팅 정책 상세
- [OpenClaw Skills](https://github.com/openclaw/openclaw/tree/main/skills) - 벤치마킹 소스

---

## 📝 Changelog

### v2.0.0 (2026-03-05)

- ✨ Installation & Dependency 필드 추가 (OpenClaw 벤치마킹)
- 📊 Runtime Metrics 실시간 수집 필드 추가
- 🔗 Versioning & Compatibility 관리 필드 추가
- 🎯 Context-Aware 라우팅 필드 추가
- 🤖 Model Fit 최적화 필드 추가
- 🔧 Validation Rules 상세화
- 📈 Migration Guide 추가

### v1.0.0 (2026-03-05)

- 초기 스키마 정의
- 필수 필드 12 개
- 선택 필드 4 개