# Registry 파싱 & 저장 Spec (v1)

작성일: 2026-03-05

---

## 1. 스킬 파일에서 메타 추출

openclaw 스킬 파일(`.md`)의 YAML frontmatter 또는 헤더 섹션에서 메타를 파싱한다.

### 1.1 파싱 대상 경로

```
~/.claude/skills/       # 글로벌 스킬
.claude/skills/         # 워크스페이스 스킬
~/.claude/agents/       # 에이전트 (별도 메타 스키마)
```

### 1.2 지원 포맷

**형식 A: YAML Frontmatter (권장)**

```markdown
---
skill_id: systematic-debugging
version: 1.2.0
status: active
domain: engineering
intents:
  - debug
  - root-cause-analysis
  - fix-error
risk_level: low
required_tools:
  - exec
  - read
  - edit
latency_class: normal
cost_class: low
conflicts: []
dependencies: []
quality_score: 0.88
owner: omc-team
last_verified_at: "2026-02-15"
---

# 스킬 본문 내용...
```

**형식 B: 헤더 주석 (레거시 지원)**

```markdown
<!-- skill:systematic-debugging v1.0.0 domain:engineering intents:debug,fix risk:low -->

# 스킬 본문 내용...
```

형식 B는 최소 필드만 파싱하고, 나머지는 기본값 적용.

### 1.3 필드 기본값 (메타 누락 시)

| 필드 | 기본값 | 추론 방법 |
|------|-------|---------|
| `skill_id` | 파일명 (확장자 제거) | `auto` |
| `version` | `0.1.0` | `auto` |
| `status` | `experimental` | `auto` |
| `domain` | `general` | `auto` |
| `intents` | 파일명 → 언더스코어 분리 | `inferred` |
| `risk_level` | `medium` | `auto` |
| `required_tools` | `[]` | `auto` |
| `latency_class` | `normal` | `auto` |
| `cost_class` | `normal` | `auto` |
| `quality_score` | `0.50` | `auto` |

---

## 2. 자동 보정 규칙 (Auto-Repair)

파싱 후 메타 품질을 자동 검사하고 보정한다.

```typescript
interface RepairRule {
  check: (meta: SkillMeta) => boolean;  // 문제 감지
  fix: (meta: SkillMeta) => SkillMeta;  // 자동 보정
  severity: 'error' | 'warning';
}

const repairRules: RepairRule[] = [
  // intents가 비어있으면 skill_id에서 추론
  {
    check: (m) => m.intents.length === 0,
    fix: (m) => ({ ...m, intents: inferIntentsFromId(m.skill_id) }),
    severity: 'warning',
  },
  // quality_score 범위 초과
  {
    check: (m) => m.quality_score < 0 || m.quality_score > 1,
    fix: (m) => ({ ...m, quality_score: 0.5 }),
    severity: 'error',
  },
  // deprecated인데 replacement 없음
  {
    check: (m) => m.status === 'deprecated' && !m.replacement_skill_id,
    fix: (m) => m, // 수정 없음, 경고만
    severity: 'warning',
  },
];
```

---

## 3. Registry 저장소

### 3.1 저장 형식: JSON + SQLite 이중화

**Primary: JSON 파일 (빠른 로드)**

```
.omc/registry/
├── skills.json          # 전체 스킬 메타 배열
├── skills.index.json    # skill_id → 파일경로 인덱스
└── embeddings/
    └── skills.vectors   # 바이너리 float32 배열 (skill_id 순서)
```

**Secondary: SQLite (쿼리/필터용)**

```sql
-- .omc/registry/registry.db

CREATE TABLE skills (
  skill_id        TEXT PRIMARY KEY,
  version         TEXT NOT NULL,
  status          TEXT NOT NULL CHECK(status IN ('active','deprecated','experimental')),
  domain          TEXT NOT NULL,
  intents         TEXT NOT NULL,  -- JSON array
  risk_level      TEXT NOT NULL CHECK(risk_level IN ('low','medium','high')),
  required_tools  TEXT NOT NULL,  -- JSON array
  latency_class   TEXT NOT NULL,
  cost_class      TEXT NOT NULL,
  conflicts       TEXT NOT NULL,  -- JSON array
  dependencies    TEXT NOT NULL,  -- JSON array
  quality_score   REAL NOT NULL,
  owner           TEXT,
  last_verified_at TEXT,
  source_path     TEXT NOT NULL,  -- 원본 .md 파일 경로
  parsed_at       TEXT NOT NULL,  -- ISO 8601
  repair_log      TEXT            -- JSON: 자동보정 내역
);

CREATE INDEX idx_status ON skills(status);
CREATE INDEX idx_domain ON skills(domain);
CREATE INDEX idx_risk_level ON skills(risk_level);
```

### 3.2 Stage A 쿼리 예시

```sql
-- 상태/툴/리스크 필터 (Stage A)
SELECT skill_id, intents, quality_score
FROM skills
WHERE status = 'active'
  AND risk_level != 'high'          -- high risk: approval token 없는 경우
  AND JSON_EACH(required_tools) ... -- required_tools 교집합 확인
  AND NOT EXISTS (
    SELECT 1 FROM JSON_EACH(conflicts) c
    WHERE c.value IN ('conflicting-skill-id')
  )
ORDER BY quality_score DESC
LIMIT 20;
```

---

## 4. 동기화 전략

### 4.1 초기 빌드

```bash
# 전체 스캔 & 레지스트리 생성
omc-registry build --paths ~/.claude/skills .claude/skills

# 출력
[+] Scanned 101 skill files
[+] Parsed: 98 / Failed: 3 / Repaired: 12
[+] Registry written to .omc/registry/
[+] Embeddings generated: 98 skills
```

### 4.2 증분 업데이트

스킬 파일이 변경될 때 해당 파일만 재파싱:

```typescript
interface SyncStrategy {
  mode: 'full' | 'incremental';
  watchPaths: string[];      // inotify / FSEvents 감시
  debounceMs: number;        // 기본 500ms
  onChanged: (path: string) => Promise<void>;
}
```

### 4.3 캐시 무효화

```typescript
// 스킬 파일 mtime이 parsed_at보다 최신이면 재파싱
function isStale(skill: SkillMeta, fileStat: fs.Stats): boolean {
  return new Date(fileStat.mtime) > new Date(skill.parsed_at);
}
```

---

## 5. Registry CLI (운영 도구)

```bash
# 전체 목록
omc-registry list --status active --domain engineering

# 충돌/중복 검사
omc-registry lint
# >> WARN: skills A, B have overlapping intents: ["debug"]
# >> ERROR: skill C is deprecated but has no replacement

# 특정 스킬 조회
omc-registry inspect systematic-debugging

# 임베딩 재생성
omc-registry embed --force
```

---

## 6. 메타 보고서 (Phase 0 deliverable)

```
.omc/registry/
└── inventory-report.md    # 스캔 결과 요약

## Inventory Report (2026-03-05)
- Total skills: 101
- Active: 87 / Deprecated: 8 / Experimental: 6
- Missing meta (auto-repaired): 12
- Conflict candidates: 4 pairs
  - [auto-orchestrate] ↔ [ultra-thin-orchestrate] (intents overlap)
  - [orchestrate] ↔ [auto-orchestrate] (intents overlap)
- Deprecated without replacement: 2
  - [ultrapilot] → replacement: autopilot
  - [pipeline] → replacement: autopilot
```
