# Cross-Platform AI Harness

Claude Code, Gemini CLI, Codex CLI가 동일한 규칙으로 동작하도록 하는 크로스 플랫폼 하네스.

규칙과 역할을 Markdown으로 한 번 작성하면, 빌드 스크립트가 각 플랫폼에 맞는 지시문(CLAUDE.md, GEMINI.md, AGENTS.md)과 설정 파일을 자동 생성합니다.

## 구조

```
harness/
├── rules/              # 공통 규칙 (Single Source of Truth)
│   ├── coding-style/   # 코딩 컨벤션
│   ├── architecture/   # 아키텍처 원칙
│   ├── framework/      # 프레임워크 규칙
│   ├── git/            # Git 워크플로우
│   ├── security/       # 보안 (deny-rules)
│   └── project/        # 프로젝트 컨텍스트
│
├── roles/              # 역할별 전문 지식
│   ├── designer.md     # Claude: 서브에이전트 / Gemini,Codex: 지시문 섹션
│   ├── backend-dev.md
│   ├── reviewer.md
│   └── pr-docs.md
│
├── templates/          # 플랫폼별 Handlebars 템플릿
├── build/              # 빌드 시스템 (parser → validator → assembler → renderer)
├── scripts/            # sync 스크립트
│
└── dist/               # 자동 생성 결과물 (커밋 대상)
    ├── claude/         # CLAUDE.md + agents/ + skills/
    ├── gemini/         # GEMINI.md + settings.json
    └── codex/          # AGENTS.md + config.json
```

## 초기 설치

### 1. 레포 클론

```bash
git clone git@github.com:team/harness.git ~/config/ai/harness
cd ~/config/ai/harness
npm install
```

### 2. Claude Code 플러그인 등록

`~/.claude/settings.json`에 추가:

```json
{
  "extraKnownMarketplaces": {
    "team-harness": {
      "source": { "source": "github", "repo": "team/harness" }
    }
  },
  "enabledPlugins": {
    "harness@team-harness": true
  }
}
```

### 3. Gemini/Codex 동기화

```bash
npm run sync
```

## 사용법

### 규칙 수정 (리드 개발자)

```bash
# 1. 규칙 파일 수정
vi rules/architecture/layered.md

# 2. 커밋 — pre-commit hook이 dist/ 자동 재생성
git add rules/
git commit -m "docs: 레이어 아키텍처 규칙 업데이트"

# 3. 푸시
git push
```

### 업데이트 받기 (팀원)

```bash
git pull
# Claude Code: 플러그인이 자동 반영
# Gemini/Codex: post-merge hook이 자동 sync
```

## 명령어

| 명령어 | 설명 |
|---|---|
| `npm run build:harness` | 전체 빌드 (dist/ 재생성) |
| `npm run build:harness -- --dry-run` | 변경 미리보기 |
| `npm run validate` | 규칙/역할 검증만 실행 |
| `npm run sync` | Gemini + Codex 동기화 |
| `npm run sync:gemini` | Gemini만 동기화 |
| `npm run sync:codex` | Codex만 동기화 |
| `npm run sync:settings` | settings.json deny rules만 병합 |
| `npm test` | 테스트 실행 |

## 규칙 파일 작성법

```markdown
---
id: my-rule                    # 고유 식별자
description: "규칙 설명"        # 한 줄 설명
section: "섹션명"               # 지시문 내 그룹핑 섹션
order: 1                       # 섹션 내 순서 (선택)
platforms: [claude, gemini]    # 적용 플랫폼 (선택, 기본: 전체)
---

## 규칙 내용

여기에 Markdown으로 규칙을 작성합니다.
```

### deny-rules 전용 형식

```markdown
---
id: deny-rules
description: "위험 명령어 차단"
section: "보안"
type: deny-rules
---

| 패턴 | 설명 |
|---|---|
| rm -rf* | 재귀 삭제 금지 |
| sudo * | 관리자 권한 금지 |
```

빌드 시 Claude는 CLAUDE.md에 텍스트로, Gemini/Codex는 settings.json에 JSON으로 변환됩니다.

## 역할 파일 작성법

```markdown
---
id: my-role                    # 고유 식별자
description: "역할 설명"
transform:
  claude: agent                # Claude: 서브에이전트로 생성
  gemini: section              # Gemini: 지시문 섹션으로 삽입
  codex: section               # Codex: 지시문 섹션으로 삽입
rules: [rule-a, rule-b]       # 참조할 규칙 id (선택)
---

역할의 상세 내용을 여기에 작성합니다.
```

`rules` 필드에 참조된 규칙은 Claude에서 스킬 폴더(`dist/claude/skills/`)로 자동 생성됩니다.

## 플랫폼별 동작 차이

| | Claude Code | Gemini CLI | Codex CLI |
|---|---|---|---|
| 배포 | 플러그인 | 파일 복사 | 파일 복사 |
| 규칙 | CLAUDE.md | GEMINI.md | AGENTS.md |
| 역할 | 서브에이전트 (.md) | 지시문 내 섹션 | 지시문 내 섹션 |
| 스킬 | skills/ 폴더 | 지시문에 인라인 | 지시문에 인라인 |
| deny rules | CLAUDE.md 텍스트 | settings.json | config.json |
| 업데이트 | 자동 (플러그인) | git pull + hook | git pull + hook |

## 프로젝트별 오버라이드

팀 공통 규칙 위에 프로젝트 고유 규칙을 추가하려면, 프로젝트 레포에 직접 배치:

```
my-project/
├── CLAUDE.md    # 프로젝트 전용 추가 지침
├── GEMINI.md
└── AGENTS.md
```

Claude Code는 홈 디렉토리 + 프로젝트 디렉토리의 CLAUDE.md를 자동 병합합니다.

## Git Hooks

| Hook | 트리거 | 동작 |
|---|---|---|
| pre-commit | `rules/`, `roles/`, `templates/` 변경 커밋 시 | `npm run build:harness` 후 dist/ 자동 스테이징 |
| post-merge | `git pull`로 규칙 변경 받을 시 | `npm run sync` 자동 실행 |
