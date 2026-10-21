---
name: agent-architecture
description: Python AI 에이전트 아키텍처 규칙 — 의존 방향(main → agent → tools → platform), 연결 창구(Protocol) 구조와 로컬/운영 구현 선택(PLATFORM), LLM과 코드의 역할 나누기, 가드레일 위치, 객체지향·DDD를 Python으로 지키는 법. 에이전트 코드를 구현하거나 리뷰할 때 참조.
---

# Agent Architecture

## 레이어와 의존 방향

```text
main.py (FastAPI, 조립)
   │
   ▼
app/agent  ──▶  app/tools  ──▶  app/domain (있을 때만)
   │               │
   ▼               ▼
app/platform (연결 창구 Protocol)  ◀──  local.py / <운영>.py (구현)
```

| 레이어 | 하는 일 | 부를 수 있는 것 |
|---|---|---|
| `main.py` | 구현을 골라 조립, API 열기 | 전부 |
| `app/agent` | 에이전트 흐름 | `tools`, `prompts`, `platform`의 Protocol |
| `app/tools` | 도구 함수 | `domain`, `platform`의 Protocol |
| `app/domain` | 업무 규칙 | 표준 라이브러리만 |
| `app/platform` | 바깥과의 연결 | 바깥 패키지 |

- 의존은 한 방향만. 안쪽(`agent`, `tools`, `domain`)은 바깥(FastAPI, 운영 플랫폼 SDK, 환경 변수)을 모른다.
- **`agent`, `tools`, `domain`에서 운영 플랫폼 SDK를 import하거나 `os.environ`을 읽으면 위반이다.**
- `agent`, `tools`는 연결 창구의 구현(`local.py` 등)이 아니라 Protocol에만 의존한다.

## 연결 창구 (app/platform)

바깥 시스템에 닿는 일은 모두 연결 창구를 거친다. 창구 하나는 `Protocol` 하나다.

| 창구 | 하는 일 | 로컬 구현 |
|---|---|---|
| LLM | 채팅 모델 객체 돌려주기 | `.env`의 OpenAI 호환 API (`langchain-openai`) |
| 프롬프트 | 이름으로 프롬프트 문장 가져오기 | `app/prompts/<이름>.md` 파일 |
| 가드레일 | 입력 검사(LLM 전), 출력 검사(LLM 후) | 그대로 통과 + 코드로 지키는 필수 규칙 |
| MCP | MCP 도구 목록 | 비어 있음 (또는 로컬 MCP 서버) |
| 지식 검색 | 질문으로 문서 조각 찾기 | 로컬 테스트용 문서 |
| 사용량 기록 | 호출·토큰 기록 | 로그 |
| 대화 기억 | 최근 대화를 일정 시간 기억 (멀티턴) | Redis (`redis` 패키지, 유지 시간 = 설계 문서) |
| 대화 기록 | 질문·답을 빠짐없이 남김 (감사) | PostgreSQL (가드레일을 거친 뒤 내용) |

- 쓰지 않는 창구는 만들지 않는다. 설계 문서의 전체 아키텍처에 있는 것만 만든다.
- 운영 플랫폼용 구현은 공개 하네스에 없다. 사용자 스킬 폴더의 플랫폼 전용 스킬에 견본이 있으면 그것을 따른다.
- 테스트는 연결 창구 자리에 가짜를 넣는다. 로컬 Redis·PostgreSQL이 꺼져 있어도 테스트는 돈다 (`python-testing`).

```python
# app/platform/ports.py
class ConversationMemory(Protocol):
    """대화 id별 최근 대화를 일정 시간 기억하는 창구."""

    async def load(self, conversation_id: str) -> list[BaseMessage]:
        """저장된 최근 대화를 돌려준다. 없거나 만료됐으면 빈 목록."""
        ...

    async def save(self, conversation_id: str, messages: list[BaseMessage]) -> None:
        """대화를 저장하고 유지 시간을 새로 시작한다."""
        ...
```

### 로컬 / 운영 구현 선택 — PLATFORM

| `PLATFORM` 값 | 쓰는 구현 |
|---|---|
| 비어 있음 / `local` | `app/platform/local.py` |
| 그 밖의 값 (예: 운영 플랫폼 이름) | `app/platform/<값>.py` |

- 운영 플랫폼의 `run-application.sh`에 `PLATFORM` 값을 적는다. 로컬에서는 비워 둔다.
- **운영용 구현을 불러오지 못하면 오류를 내고 서버를 멈춘다.** 로컬 구현으로 조용히 바꾸지 않는다 (운영에서 가짜 답이 나가는 사고를 막는다).
- 자동 감지(패키지가 있으면 운영용)는 쓰지 않는다.
- 고르는 곳은 `app/platform/__init__.py`의 `build_platform()` 한 곳이다. `main.py`가 서버 시작 때 한 번 부른다.

```python
def build_platform(settings: Settings | None = None) -> Platform:
    """PLATFORM 환경 변수에 맞는 연결 창구 묶음을 만든다."""
    settings = settings or load_settings()
    name = settings.platform or "local"
    try:
        module = importlib.import_module(f"app.platform.{name}")
    except ImportError as e:
        raise PlatformLoadError(f"연결 창구를 불러오지 못했다: PLATFORM={name}") from e
    return module.create_platform(settings)
```

## LLM과 코드의 역할 나누기

| LLM이 맡는 일 | 코드(도구·도메인)가 맡는 일 |
|---|---|
| 질문 이해, 어떤 도구를 쓸지 판단 | 금액 계산, 날짜 판단, 권한 확인 |
| 결과를 자연스러운 문장으로 정리 | 외부 시스템 조회·변경 |
| | 답이 하나여야 하는 모든 일 |

## 가드레일 위치

```text
질문 → [입력 가드레일] → LLM·도구 → [출력 가드레일] → 답
```

- 입력 검사는 LLM을 부르기 전, 출력 검사는 LLM이 답한 뒤에 한다.
- **꼭 지켜야 하는 규칙(개인정보 가리기, 금지 답변)은 프롬프트가 아니라 코드에 둔다.** LLM은 프롬프트를 어길 수 있다.
- 대화 기록에는 가드레일을 거친 뒤 내용을 남긴다.

## 프롬프트

- 프롬프트 문장을 코드 안에 직접 쓰지 않는다. `app/prompts/<이름>.md` 파일로 두고 프롬프트 창구로 가져온다.
- 바뀌는 값은 `{변수}` 자리로 두고 코드에서 채운다.

## 객체지향 — Python에서 지키는 법

`core:oop-principles`의 원칙을 Python으로 옮긴 표다.

| 원칙 | Python에서 |
|---|---|
| 추상화 (인터페이스) | `typing.Protocol`로 모양을 정한다 (Java interface 역할). 상속하지 않아도 모양이 맞으면 된다 |
| 의존성 역전 (DIP) | `agent`, `tools`는 Protocol에만 의존한다. 구현은 바깥에서 넣어 준다 |
| 의존성 주입 | `main.py` 한 곳에서 구현을 골라 조립해 넘겨준다 (Spring이 해 주던 일을 직접). 함수 안에서 구현을 직접 만들지 않는다 |
| 캡슐화 | 밖에서 쓰지 않는 것은 `_`로 시작한다. 값 묶음은 `@dataclass(frozen=True)`. 내부 리스트는 복사본이나 `tuple`로 돌려준다 |
| 다형성 | `isinstance` 분기가 반복되면 Protocol 구현을 나눈다 |
| 조합 > 상속 | 기능을 상속으로 물려받지 않고, 필요한 객체를 인자로 받아서 쓴다 |
| 객체 생성 | 검증은 `__post_init__`. 생성자를 바로 불러도 된다. 만드는 상황마다 채우는 값이 다를 때만 `create()`/`restore()` (`python-style`) |

Python에는 `private`, `final`, `new`가 없다. Java 문법을 흉내 내지 않는다 (예: 생성자를 막으려고 `__new__`를 건드리지 않는다).

## DDD — 업무 규칙이 있을 때만

에이전트는 보통 "질문 → LLM 판단 → 도구로 외부 시스템 호출 → 답" 흐름이라 내 코드 안의 업무 규칙이 얇다. 그래서 **계산·판단·상태 변화 같은 규칙이 있을 때만** `app/domain/`을 만든다. 외부 시스템을 불러 주기만 하는 도구뿐이면 만들지 않는다. designer가 설계 문서에 업무 규칙 유무를 적는다.

| DDD 개념 | Python에서 |
|---|---|
| 값 객체 | `@dataclass(frozen=True)` + `__post_init__` 검증 |
| 엔티티 | id를 가진 클래스. 상태는 의미 있는 메서드로만 바꾼다 |
| 애그리거트 | 엔티티 묶음. 바깥은 루트를 통해서만 접근 |
| 리포지토리 | `Protocol`로 모양을 정하고 구현은 `app/platform/`에 |
| 도메인 서비스 | 한 객체에 넣기 애매한 규칙을 담는 함수 |

`app/domain/`은 LangChain, FastAPI, pydantic 같은 바깥 패키지를 import하지 않는다.
