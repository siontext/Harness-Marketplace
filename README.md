# Team Harness

Claude Code용 에이전트 하네스 마켓플레이스. 공통 플러그인(`core`)과 언어별 플러그인(`java`, `python`)으로 나뉘며, 프로젝트 언어에 맞는 플러그인만 켜서 쓴다.

빌드 단계가 없다. `plugins/` 아래 파일이 그대로 배포된다.

## 구조

```
.claude-plugin/marketplace.json   플러그인 목록
plugins/
├── core/                         공통 — 모든 프로젝트에서 켬
│   ├── agents/                   designer, pr-docs
│   ├── skills/                   design-doc, agent-design-doc, implementation-checkpoint,
│   │                             oop-principles, general-style, git-conventions,
│   │                             commit-splitting, team-workflow
│   └── hooks/                    위험 명령 차단 (deny-guard.py + deny-rules.json)
├── java/                         Java/Kotlin/Spring Boot 프로젝트
│   ├── agents/                   backend-dev, java-reviewer
│   └── skills/                   java-style, kotlin-style, java-testing, kotlin-testing,
│                                 spring-boot-conventions, layered-architecture, api-verification
└── python/                       Python AI 에이전트 (LangGraph·FastAPI) 프로젝트
    ├── agents/                   python-dev, python-reviewer
    ├── skills/                   python-style, python-project, python-testing,
    │                             agent-architecture, langgraph-conventions, fastapi-conventions
    │                             + 명령: new, export, eval (직접 부를 때만)
    ├── scripts/                  export.py, eval_check.py, eval_run.py
    └── hooks/                    반출 전용 프로젝트의 git push·remote 추가 차단
```

## 설치

`~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "team-harness": {
      "source": { "source": "github", "repo": "siontext/Harness-Marketplace" }
    }
  },
  "enabledPlugins": {
    "core@team-harness": true,
    "java@team-harness": true,
    "python@team-harness": true
  }
}
```

프로젝트마다 다르게 켜려면 프로젝트의 `.claude/settings.json`에 `enabledPlugins`를 둔다.

### 1.x(`harness@team-harness`)에서 옮기기

1. `enabledPlugins`에서 `harness@team-harness`를 지우고 `core@team-harness`, `java@team-harness`를 추가한다.
2. `/plugin`에서 마켓플레이스를 업데이트한다.
3. 스킬 이름 앞부분이 바뀐다: `harness:design-doc` → `core:design-doc`, `harness:java-style` → `java:java-style`.
4. 에이전트 이름 변경: `reviewer` → `java-reviewer`.

Gemini·Codex 동기화는 2.0에서 없앴다. 이전 버전이 `~/.gemini`, `~/.codex`에 복사해 둔 파일은 그대로 남아 있으니 필요 없으면 직접 지운다.

## 수정하기

- 스킬: `plugins/<플러그인>/skills/<이름>/SKILL.md`. frontmatter는 `name`, `description`.
- 에이전트: `plugins/<플러그인>/agents/<이름>.md`. `skills:`에 같은 플러그인 스킬은 이름만, 다른 플러그인 스킬은 `core:design-doc`처럼 플러그인 이름을 붙인다.
- 바꾼 뒤 `marketplace.json`과 해당 플러그인 `plugin.json`의 `version`을 올린다. 버전이 같으면 설치된 쪽이 갱신되지 않는다.
- 로컬에서 바로 시험: `claude --plugin-dir plugins/core --plugin-dir plugins/java --plugin-dir plugins/python`
- 검사: `claude plugin validate .`

플러그인 루트의 `CLAUDE.md`는 Claude Code가 읽지 않는다. 항상 적용할 지시문은 스킬로 만든다.

## 위험 명령 차단

`plugins/core/hooks/deny-rules.json`이 규칙의 단일 원천이다. `PreToolUse` 훅이 Bash 명령을 검사해 차단한다.

```json
{
  "pattern": "git push --force*",
  "description": "강제 푸시 금지",
  "alternative": "git push --force-with-lease 사용",
  "exceptions": ["git push --force-with-lease*"]
}
```

- **pattern**: `*`는 임의 문자열. 명령 경계(줄 시작, `;` `&&` `|` `(` 따옴표 뒤)에서 매칭하므로 복합 명령에 숨겨도 잡힌다.
- **exceptions**: 같은 규칙에 걸려도 허용할 명령.
- 판단이 애매하면 차단 쪽으로 기운다. 오탐은 재시도 한 번이면 되지만 미탐은 되돌릴 수 없다.

규칙을 바꿀 때 `deny-guard.py`는 손대지 않는다.

## Python 프로젝트

로컬(맥)에서 개발·테스트하고, 소스를 압축 파일로 운영 플랫폼에 옮기는 방식을 기준으로 한다.

| 명령 | 하는 일 |
|---|---|
| `/python:new [경로]` | 고정 뼈대 + uv로 Python 3.11.15 가상환경 + 로컬 git |
| `/python:export [경로]` | Ruff·Pyrefly·pytest(커버리지 80%)·키 섞임 검사 통과 후 zip |
| `/python:eval [질문 id]` | 연결 확인 → 비용 확인 → 로컬 서버 `/chat`으로 평가 질문 실행 |

- 명령은 `disable-model-invocation`이라 Claude가 알아서 실행하지 않는다.
- `run-application.sh`가 있는 프로젝트는 반출 전용으로 보고 `git push`, `git remote add`를 훅이 막는다.
- 바깥 시스템은 연결 창구(`app/platform/`의 Protocol)로만 부른다. 공개 하네스에는 Protocol과 로컬 구현만 있다. 운영 플랫폼 구현 견본은 사용자 스킬 폴더의 `templates/project/`에 두면 `/python:new`가 덮어 복사한다.

## 프로젝트·사용자 전용 스킬

공개하면 안 되는 플랫폼 전용 규칙은 이 레포에 넣지 않고 사용자 스킬 폴더(`~/.claude/skills/<이름>/SKILL.md`)에 둔다. `designer`는 이 폴더에서 플랫폼 전용 설계 스킬을 찾아 따른다.
