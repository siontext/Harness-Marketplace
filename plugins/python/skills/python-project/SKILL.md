---
name: python-project
description: Python AI 에이전트 프로젝트 구성 — 고정 폴더 구성, pyproject.toml(실행·개발 패키지 분리, Ruff·Pyrefly·pytest 설정), uv로 Python 3.11 가상환경과 버전 고정 설치, .env 관리, 반출 제외 목록, 로컬 전용 git. 프로젝트를 만들거나 설정·의존성·폴더를 바꿀 때 참조.
---

# Python Project Guide

로컬(맥)에서 개발·테스트하고, 소스를 압축해 운영 플랫폼으로 옮기는 프로젝트를 기준으로 한다. 운영 플랫폼은 오프라인이라 **이미 설치된 패키지만** 쓸 수 있다.

새 프로젝트는 `/python:new`로 만든다. 뼈대 파일의 원본은 `${CLAUDE_PLUGIN_ROOT}/skills/new/template/`이다.

## 폴더 구성 (고정)

```text
<프로젝트>/
├── main.py                  FastAPI 앱 — 연결 창구 조립, /chat, /health
├── run-application.sh       운영 플랫폼에서 서버를 띄우는 스크립트
├── pyproject.toml           패키지·도구 설정
├── constraints.txt          운영 플랫폼 패키지 버전 고정 파일 (있을 때)
├── .env.example             환경 변수 견본 (값 없음) — 공유
├── .env                     실제 값 — git·반출 제외
├── app/
│   ├── agent/               에이전트 흐름 (create_agent / StateGraph)
│   ├── tools/               도구 함수 (@tool)
│   ├── prompts/             프롬프트 파일 (.md)
│   ├── platform/            연결 창구 — Protocol, 로컬 구현, 설정
│   └── domain/              업무 규칙 (있을 때만)
├── tests/                   pytest — 반출에 포함
└── evals/                   평가 질문 (results/는 반출 제외)
```

- 새 폴더를 만들지 않는다. 필요하면 위 폴더 안에 모듈을 추가한다.
- `app/domain/`은 계산·판단·상태 변화 같은 업무 규칙이 있을 때만 만든다 (`agent-architecture`).
- 각 폴더에 `__init__.py`를 둔다.

## pyproject.toml

| 칸 | 내용 |
|---|---|
| `requires-python` | `">=3.11,<3.12"` — 운영 플랫폼과 같은 3.11 |
| `dependencies` | 실행에 필요한 패키지. **운영 플랫폼에 설치된 것만** 적는다 |
| `optional-dependencies.dev` | 개발할 때만 쓰는 것: `pytest`, `pytest-cov`, `ruff`, `pyrefly` |
| `tool.ruff` | 88자, `py311`, 검사 규칙 묶음 |
| `tool.pyrefly` | 검사 대상 폴더, Python 3.11 |
| `tool.pytest.ini_options` | `testpaths`, `pythonpath`. **커버리지 옵션(`--cov`)은 넣지 않는다** |

- 버전은 `pyproject.toml`에 적지 않고 `constraints.txt`로 고정한다. 범위만 적는다 (예: `"langgraph"`).
- 커버리지 도구는 운영 플랫폼에 없을 수 있다. `pyproject.toml`에 `--cov`를 넣으면 운영 플랫폼의 테스트 실행이 깨진다. 커버리지는 python-reviewer와 `/python:export`가 실행할 때만 붙인다.
- 프로젝트 자체는 패키지로 설치하지 않는다. `pythonpath = ["."]`로 `app`을 찾는다.

Ruff 설정:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "SIM", "N", "ASYNC", "G", "T20", "RUF"]
ignore = ["RUF001", "RUF002", "RUF003"]  # 한글 문장의 전각 문자 경고
```

## 설치 (로컬)

uv는 Python 설치와 가상환경 생성에만 쓴다. 패키지 목록은 표준 형식(`pyproject.toml` + 고정 파일)으로 관리하고 `uv.lock`은 만들지 않는다. 운영 플랫폼은 pip을 쓰기 때문이다.

```bash
uv python install 3.11.15
uv venv --python 3.11.15 .venv
uv pip install --python .venv -r pyproject.toml --extra dev -c constraints.txt
```

- `uv run`, `uv sync`, `uv add`는 쓰지 않는다. `uv.lock`을 만든다.
- 명령은 가상환경 경로로 실행한다: `.venv/bin/pytest`, `.venv/bin/ruff`, `.venv/bin/pyrefly`.
- `constraints.txt`가 없으면 `-c`를 빼고 설치하되, 운영 플랫폼과 버전이 달라질 수 있다고 사용자에게 알린다.
- 패키지를 추가할 때는 먼저 운영 플랫폼에 있는지(고정 파일에 있는지) 확인한다. 없으면 추가하지 않고 사용자에게 알린다.

## 환경 변수 (.env)

| 이름 | 뜻 |
|---|---|
| `PLATFORM` | 연결 창구 선택. 비우면 로컬 (`agent-architecture`) |
| `LLM_BASE_URL` | 로컬 LLM 주소 (OpenAI 호환) |
| `LLM_API_KEY` | 로컬 LLM 키 |
| `LLM_MODEL` | 모델 이름 |
| `REDIS_URL` | 대화 기억 저장소 |
| `DATABASE_URL` | 대화 기록 저장소 (PostgreSQL) |

- `.env.example`(값이 빈 견본)만 git에 넣는다. `.env`는 git과 반출에서 뺀다.
- `.env`는 `app/platform/settings.py`가 로컬에서만 읽는다. 다른 모듈에서 `os.environ`을 읽지 않는다.
- 테스트는 `.env`를 읽지 않는다. 연결 창구 자리에 가짜를 넣는다 (`python-testing`).

## 실행

| 어디서 | 명령 |
|---|---|
| 로컬 | `.venv/bin/uvicorn main:app --reload` |
| 운영 플랫폼 | `run-application.sh` (플랫폼 실행 방식에 맞춘다) |

## 반출 제외 목록

`/python:export`가 이 목록을 그대로 쓴다 (`${CLAUDE_PLUGIN_ROOT}/scripts/export.py`의 `EXCLUDES`).

| 제외 | 이유 |
|---|---|
| `.git/` | 로컬 변경 기록 |
| `.env`, `.env.*` (`.env.example` 제외) | 키 |
| `.venv/` | 로컬 가상환경 |
| `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/` | 캐시 |
| `.coverage`, `htmlcov/`, `coverage.xml` | 커버리지 결과 |
| `evals/results/` | 평가 결과 |
| `docs/` | 설계·리뷰 문서 (로컬 git에만 남긴다) |
| `.DS_Store`, `.idea/`, `.vscode/` | 편집기·OS 파일 |

`tests/`는 포함한다. 운영 플랫폼에서도 테스트가 돌기 때문이다.

## git — 로컬 전용

- 변경 기록용으로 로컬 git만 쓴다. **원격 저장소를 연결하지 않는다.**
- `run-application.sh`가 있는 프로젝트에서는 python 플러그인 훅이 `git push`와 `git remote add`를 막는다.
- 소스는 `/python:export`로 만든 압축 파일로만 옮긴다.
