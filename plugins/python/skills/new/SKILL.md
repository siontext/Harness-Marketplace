---
name: new
description: 정해진 뼈대로 새 Python AI 에이전트 프로젝트를 만든다 — 폴더·main.py·연결 창구·테스트 견본, uv로 Python 3.11.15 가상환경, 패키지 설치, 로컬 git 시작. 사용자가 /python:new를 직접 칠 때만 실행한다.
disable-model-invocation: true
argument-hint: "[프로젝트 경로]"
---

# 새 프로젝트 만들기

`python-project` 스킬의 고정 구성으로 새 프로젝트를 만든다. 뼈대 원본은 이 스킬 폴더의 `template/`이다 (`${CLAUDE_SKILL_DIR}/template`, 비어 있으면 `~/.claude/plugins/marketplaces/team-harness/plugins/python/skills/new/template`).

인자: `$ARGUMENTS` — 만들 프로젝트 경로. 없으면 사용자에게 묻는다.

## 절차

각 단계의 결과를 한 줄씩 사용자에게 알린다. 실패하면 멈추고 원인과 다음 할 일을 알린다.

### 1. 대상 폴더 확인

- 경로가 이미 있고 비어 있지 않으면 멈춘다. 덮어쓰지 않는다.
- 프로젝트 이름은 폴더 이름을 쓴다. `pyproject.toml`의 `name`을 이 이름(소문자, `-` 연결)으로 바꾼다.

### 2. 뼈대 복사

- `template/`의 내용을 대상 폴더로 복사한다 (`cp -R <template>/. <대상>`).
- 이름 바꾸기: `gitignore` → `.gitignore`, `env.example` → `.env.example`.
- `.env.example`을 복사해 `.env`를 만든다 (값은 비어 있음).

### 3. 플랫폼 전용 견본 덮어쓰기 (있을 때만)

- 사용자 스킬 폴더에서 `~/.claude/skills/*/templates/project/`를 찾는다.
- 있으면 그 내용을 대상 폴더에 덮어 복사한다. 운영용 연결 창구(`app/platform/<이름>.py`), `run-application.sh`, `constraints.txt` 등이 들어온다.
- 여러 개면 어느 것을 쓸지 사용자에게 묻는다. 없으면 건너뛰고 "운영 플랫폼용 연결 창구는 직접 추가해야 한다"고 알린다.
- **이 견본의 내용을 공개 저장소나 하네스에 옮기지 않는다.**

### 4. Python과 가상환경

- `command -v uv`로 uv가 있는지 본다. 없으면 멈추고 설치 방법(`brew install uv`)을 안내한다. 직접 설치하지 않는다.
- 대상 폴더에서:

```bash
uv python install 3.11.15
uv venv --python 3.11.15 .venv
uv pip install --python .venv -r pyproject.toml --extra dev -c constraints.txt
```

- `constraints.txt`가 없으면 `-c constraints.txt`를 빼고 설치한 뒤 "운영 플랫폼과 패키지 버전이 다를 수 있다"고 알린다.
- `uv run`, `uv sync`는 쓰지 않는다 (`uv.lock`을 만든다).

### 5. 뼈대 검사

대상 폴더에서 차례로 실행해 모두 통과하는지 확인한다.

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/pyrefly check
.venv/bin/pytest -q
```

### 6. 로컬 git 시작

```bash
git init
git add -A
git commit -m "chore : 프로젝트 생성"
```

- 원격 저장소(`git remote add`)는 연결하지 않는다. python 플러그인 훅이 막는다.
- `git status`로 `.env`가 커밋되지 않았는지 확인한다.

### 7. 다음 할 일 안내

- `.env`에 로컬 LLM 주소·키·모델을 채운다.
- 설계는 `designer` 에이전트에게 맡긴다 (AI 에이전트 양식 `agent-design-doc`).
- 로컬 실행: `.venv/bin/uvicorn main:app --reload` → `http://127.0.0.1:8000/health`
