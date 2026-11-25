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
├── main.py                  부트스트랩 — FastAPI 앱 만들기, lifespan에서 조립(Container) 부르기, 전역 예외 핸들러 등록, 라우터 붙이기
├── run-application.sh       운영 플랫폼에서 서버를 띄우는 스크립트
├── pyproject.toml           패키지·도구 설정
├── constraints.txt          운영 플랫폼 패키지 버전 고정 파일 (있을 때)
├── .env.example             환경 변수 견본 (값 없음) — 공유
├── .env                     실제 값 — git·반출 제외
├── app/
│   ├── common/              모든 계층이 같이 쓰는 것 — errors.py(공통 예외). 표준 라이브러리만
│   ├── container.py         조립(Container) — 구현을 골라 서비스·도구·에이전트에 넣어 주기
│   ├── presentation/        웹 레이어 — routes.py(엔드포인트), schemas.py(요청·응답 내용), exception/(전역 예외 핸들러·오류 대응표·실패 로그)
│   │   └── response/        공통 응답 틀 — ApiResponse, SseEvent, SseResponse, ErrorCode, 안내 문구
│   ├── application/
│   │   ├── common/          기능의 규칙 없이 쓰는 기술 도우미 — time_limit.py(TimeLimit), sentences.py(SentenceSplitter)
│   │   ├── agent/           채팅 기능 — usecase.py(ChatUseCase), service.py(ChatService), port.py(AnswerGenerator·Guardrail), dto/command.py(ChatCommand). LangChain을 모른다
│   │   └── <기능>/          업무 기능 하나 — usecase.py, port.py, service.py, dto/(command.py, result.py)
│   ├── domain/
│   │   └── <기능>/          도메인 객체(규칙이 없으면 값만), 업무 규칙, 코드값 Enum, 업무 예외
│   ├── infrastructure/      포트 구현 — __init__.py(Platform·구현 선택), local.py(LocalPlatformFactory), settings.py(Settings)
│   │   ├── agent/           답 만들기 어댑터 — create_agent 조립, LangGraph 메시지를 글자로 번역, LLM 실패 미들웨어
│   │   ├── llm/             LLM 창구 모양(port.py)과 구현
│   │   ├── persistence/     저장소 구현(DB·메모리) — <기능>/ 폴더마다 (있을 때만)
│   │   ├── client/          외부 API를 부르는 구현 — <기능>/ 폴더마다 (있을 때만)
│   │   ├── prompt/          프롬프트 창구 모양(port.py)과 구현
│   │   ├── guardrail/       가드레일 구현
│   │   └── tools/           도구 클래스 (<기능>Tools — 메서드를 tool()로 감싼다)
│   └── prompts/             프롬프트 파일 (.md)
├── tests/                   pytest — app/ 아래 폴더 구조를 그대로 따른다 (python-testing), 반출에 포함
└── evals/                   평가 질문 (results/는 반출 제외)
```

- 새 폴더를 만들지 않는다. 필요하면 위 폴더 안에 모듈을 추가한다.
- FastAPI를 import하는 코드는 `main.py`와 `app/presentation/`에만 둔다 (`agent-architecture`).
- `app/` 바로 아래에 두는 모듈은 `container.py` 하나다. 더 생기면 사용자에게 확인한다.
- **공통은 두 단계로 나눈다** (`agent-architecture`의 "공통 영역"). 모든 계층이 쓰는 것은 `app/common/`, 한 계층 안에서 여러 기능이 쓰는 것은 그 계층의 `common/`(presentation은 `response/`)에 둔다.
- `infrastructure/` 아래는 창구 종류마다 폴더 하나다. 새 종류의 창구가 생기면 폴더를 더한다 (예: `memory/`).
- 업무 기능이 생기면 `application/<기능>/`, `domain/<기능>/`, 구현 폴더(`infrastructure/persistence/<기능>/` 또는 `infrastructure/client/<기능>/`)를 같은 이름으로 만든다 (`agent-architecture`의 "기능 폴더").
- `domain/<기능>/`은 업무 규칙이 없어도 만든다. 규칙이 없으면 값만 갖는 도메인 객체와 업무 예외(대상 없음)를 둔다 (`agent-architecture`의 "DDD").
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
- 로컬에 없는 SDK를 import하는 운영 플랫폼 구현(`app/infrastructure/<이름>.py`)은 `[tool.pyrefly] project-excludes`와 `[tool.coverage.run] omit`에 넣는다. 운영 플랫폼에서는 그대로 쓰인다.

Ruff 설정:

```toml
[tool.ruff]
line-length = 88
target-version = "py311"
# Ruff 0.17은 .md 안의 파이썬 코드 블록도 포맷한다. 설계 문서와 프롬프트는 건드리지 않는다.
extend-exclude = ["docs", "app/prompts"]

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
| `AGENT_TIMEOUT_SECONDS` | 질문 하나의 전체 시간 제한(초). 비우면 30. 0 이하면 서버가 뜨지 않는다 (`fastapi-conventions`의 "시간 제한") |
| `REDIS_URL` | 대화 기억 저장소 |
| `DATABASE_URL` | 대화 기록 저장소 (PostgreSQL) |

- `.env.example`(값이 빈 견본)만 git에 넣는다. `.env`는 git과 반출에서 뺀다.
- 환경 변수와 `.env`는 `app/infrastructure/settings.py`의 `Settings`(`pydantic-settings`의 `BaseSettings`)만 읽는다. `Settings()`로 만들면 칸 이름을 대문자로 바꾼 환경 변수에서 값을 읽고(`llm_model` ← `LLM_MODEL`), 로컬에서는 `.env`도 함께 읽는다. 환경 변수가 `.env`보다 우선한다. 다른 모듈에서 `os.environ`을 읽지 않는다.
- 환경 변수를 더할 때는 `Settings`에 칸 한 줄(타입과 기본값)을 더하고 `.env.example`에 이름을 적는다. `.env`를 직접 읽거나 값을 바꾸는 코드를 쓰지 않는다. 값의 범위는 `Field(gt=0)`처럼 칸에 적는다.
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
| `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/` | 캐시 |
| `dist/`, `build/` | 빌드 결과 |
| `.coverage`, `htmlcov/`, `coverage.xml` | 커버리지 결과 |
| `evals/results/` | 평가 결과 |
| `docs/` | 설계·리뷰 문서 (로컬 git에만 남긴다) |
| `.DS_Store`, `.idea/`, `.vscode/` | 편집기·OS 파일 |

`tests/`는 포함한다. 운영 플랫폼에서도 테스트가 돌기 때문이다.

## git — 로컬 전용

- 변경 기록용으로 로컬 git만 쓴다. **원격 저장소를 연결하지 않는다.**
- `run-application.sh`가 있는 프로젝트에서는 python 플러그인 훅이 `git push`와 `git remote add`를 막는다.
- 소스는 `/python:export`로 만든 압축 파일로만 옮긴다.
