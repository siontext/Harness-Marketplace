---
name: agent-architecture
description: Python AI 에이전트 아키텍처 규칙 — 4계층(presentation / application / domain / infrastructure)과 포트·어댑터 의존 방향, 업무 서비스와 도구의 역할, 조립(app/container.py), 공통 예외(app/errors.py) 위치, 연결 창구(Protocol) 구조와 로컬/운영 구현 선택(PLATFORM), LLM과 코드의 역할 나누기, 가드레일 위치, 객체지향·DDD를 Python으로 지키는 법. 에이전트 코드를 구현하거나 리뷰할 때 참조.
---

# Agent Architecture

## 레이어와 의존 방향

4계층에 포트·어댑터를 더한 구조다. Java 하네스(`java:layered-architecture`)와 같은 이름을 쓴다.

```text
main.py ──▶ app/container.py (조립: 구현을 골라 연결)

app/presentation      FastAPI — 엔드포인트, 요청·응답, 전역 예외 핸들러
        │
        ▼
app/application       에이전트 흐름(agent/), 업무 서비스, 포트(ports.py)
        │                          ▲
        ▼                          │ 포트를 구현 · 서비스를 호출
app/domain            업무 규칙     │
                                   │
app/infrastructure    LLM·저장소·프롬프트·가드레일 구현, 도구(tools/)

app/errors.py (공통 예외)  ◀──  모든 레이어
```

| 레이어 | 두는 것 | import할 수 있는 프로젝트 코드 |
|---|---|---|
| `app/presentation` | 엔드포인트, 요청·응답 모델, 공통 응답 틀, 전역 예외 핸들러 | `application`, `app/errors.py` |
| `app/application/agent/` | 에이전트 조립과 실행 흐름 (입력 검사 → 실행 → 출력 검사, 시간 제한) | `application` 안, `domain`, `app/errors.py` |
| `app/application/<이름>_service.py` | 업무 서비스 — 꺼내기 → 도메인 호출 → 저장 같은 순서 | `application/ports.py`, `domain`, `app/errors.py` |
| `app/application/ports.py` | 포트 — 바깥에 요구하는 모양 (`Protocol`) | `domain` |
| `app/domain` | 업무 규칙 (있을 때만) | `app/errors.py`만 |
| `app/infrastructure` | 포트 구현(어댑터), 도구, 설정, 구현 선택 | `application`, `domain`, `app/errors.py` |
| `app/container.py` | 조립 — 구현을 서비스·도구·에이전트에 넣어 주기 | 전부 |
| `main.py` | `FastAPI` 앱 만들기, `lifespan`에서 조립 함수 부르기 | 전부 |
| `app/errors.py` | 공통 예외 | 표준 라이브러리만 |

- **`application`과 `domain`은 `infrastructure`와 `presentation`을 import하지 않는다.** 위반이면 불통과다.
- `presentation`은 `infrastructure`를 import하지 않는다. 필요한 것은 `container.py`가 만들어 `app.state`에 둔다.
- `infrastructure`와 `application`을 함께 아는 곳은 `container.py`(와 그것을 부르는 `main.py`)뿐이다.
- `application`, `domain`에서 운영 플랫폼 SDK를 import하거나 `os.environ`을 읽으면 위반이다.

### 바깥 패키지를 쓸 수 있는 곳

| 패키지 | 쓸 수 있는 곳 |
|---|---|
| FastAPI | `main.py`, `app/presentation` |
| LangChain·LangGraph | `app/application/agent/`, `app/application/ports.py`(채팅 모델 타입), `app/infrastructure` |
| 운영 플랫폼 SDK, DB·Redis 클라이언트 | `app/infrastructure` |
| 없음 (표준 라이브러리만) | `app/domain`, `app/application/<이름>_service.py` |

에이전트 루프는 LangChain이 돌려 주므로 에이전트 조립 코드는 LangChain을 쓴다. 업무 서비스와 도메인은 LangChain을 모르게 두어, 프레임워크를 바꾸거나 같은 기능을 다른 창구(REST 등)로 열어도 그대로 쓸 수 있게 한다.

## Command — presentation에서 application으로 넘기는 값

`presentation`은 요청 모델을 그대로 넘기지 않고 Command로 바꿔 넘긴다. Java 하네스의 Command와 같은 역할이다.

```python
# app/application/agent/chat_command.py
@dataclass(frozen=True)
class ChatCommand:
    """에이전트에 넘기는 질문 한 건."""

    conversation_id: str
    message: str


# app/presentation/routes.py
command = ChatCommand(conversation_id=body.conversation_id, message=body.message)
```

- Command는 `app/application`에 두는 변하지 않는 값 묶음이다 (`@dataclass(frozen=True)`). pydantic을 쓰지 않는다. 형식 검사는 요청 모델이 이미 했다.
- `application`은 요청 모델(`ChatRequest`)을 모른다. 넘길 값이 늘면 Command에 칸을 더하고 함수 모양은 그대로 둔다.
- 바꾸는 곳은 `app/presentation/routes.py`다.

## 업무 서비스와 도구

도구는 LLM이 시스템을 부르는 창구다. 도구 안에 업무 순서를 직접 적지 않고 **항상 업무 서비스를 거친다.**

| 파일 | 맡는 일 | 모르는 것 |
|---|---|---|
| `app/domain/` | 판단·계산 (예: 취소할 수 있는가) | 저장소, LLM, 문장 |
| `app/application/<이름>_service.py` | 순서 (꺼내기 → 도메인에 판단 맡기기 → 저장). 결과는 값이나 예외로 알린다 | LangChain, LLM이 읽을 문장 |
| `app/infrastructure/tools/` | 서비스 호출, 결과와 예외를 LLM이 읽을 문장으로 바꾸기 | 판단, 순서 |

```python
# app/application/order_service.py
class OrderService:
    def __init__(self, orders: OrderRepository, now: Callable[[], datetime]) -> None:
        self._orders = orders
        self._now = now

    async def cancel_order(self, order_id: str) -> Order:
        order = await self._orders.find(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        cancelled = order.cancel(self._now())      # 판단은 도메인
        await self._orders.save(cancelled)
        return cancelled
```

- 조회처럼 전달만 하는 기능도 서비스를 거친다. 서비스가 한 줄이어도 도구가 포트를 직접 부르지 않는다. 기준이 하나여야 도구마다 판단이 갈리지 않는다.
- 서비스는 포트와 "지금 시각" 같은 바뀌는 값을 생성자로 받는다. 안에서 시계를 읽거나 구현을 만들지 않는다.
- 도구가 예외를 문장으로 바꾸는 규칙은 `langgraph-conventions`의 "도구 만들기"를 따른다.

## 조립 (app/container.py)

```python
def build_agent_context(platform: Platform, timeout_seconds: float) -> AgentContext:
    service = OrderService(platform.orders, _read_utc_now)
    agent = build_order_agent(
        model=platform.llm.chat_model(),
        tools=build_order_tools(service),
        system_prompt=platform.prompts.get("system"),
    )
    return AgentContext(agent, platform.guardrail, timeout_seconds)
```

- 구현 → 서비스 → 도구 → 에이전트 순서로 넣어 준다. 조립 함수는 `container.py`에만 둔다.
- `main.py`의 `lifespan`이 `build_platform()`으로 구현 묶음을 만들고 조립 함수를 불러 결과를 `app.state`에 둔다.
- 테스트는 가짜 구현 묶음을 같은 조립 함수에 넣는다. 테스트용 조립 코드를 따로 만들지 않는다.

## 예외 위치

예외는 던진 곳에서 호출한 쪽으로 올라가고, 아무도 잡지 않으면 FastAPI가 잡아 전역 핸들러에 넘긴다. 그래서 던지는 쪽과 응답으로 바꾸는 쪽을 나눈다.

| 무엇 | 위치 | 이유 |
|---|---|---|
| 여러 레이어가 던지거나 전역 핸들러가 구분해 답하는 예외 (`AppError`, `UpstreamError`, `AgentTimeoutError`) | `app/errors.py` | 안쪽 레이어가 import해야 하므로 HTTP를 몰라야 한다 |
| 한 레이어 안에서만 쓰는 예외 (예: `PlatformLoadError`) | 그 레이어 안 | 밖에서 구분할 일이 없다 |
| 업무 규칙에 걸렸을 때 던지는 예외 (예: `OrderNotCancellableError`, `OrderNotFoundError`) | `app/domain/` (규칙 옆) | 도구가 잡아 문장으로 바꾼다. 전역 핸들러까지 가지 않는다 |
| 예외 → 상태 코드·`code`·안내 문구 대응표, 전역 핸들러 | `app/presentation/errors.py` | HTTP 응답을 만드는 일이다 (`fastapi-conventions`) |
| `code` 값(`ErrorCode`), 안내 문구 | `app/presentation/response/` | 호출하는 쪽에 보이는 응답의 일부다 |

- 예외 클래스에 상태 코드나 `code`를 넣지 않는다. 대응은 `app/presentation/errors.py`의 표 한 곳에만 둔다.
- 새 예외는 `AppError`나 그 하위 예외를 상속한다. 대응표에 없으면 가장 가까운 부모의 규칙으로 답한다.

## 연결 창구 — 포트와 구현

바깥 시스템에 닿는 일은 모두 연결 창구를 거친다. 창구 하나는 `Protocol` 하나다. 모양(포트)은 `app/application/ports.py`에, 구현(어댑터)은 `app/infrastructure/`에 둔다.

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
- 구현은 창구 종류마다 폴더 하나에 둔다: `infrastructure/llm/`, `persistence/`, `prompt/`, `guardrail/`. 도구는 `infrastructure/tools/`.
- **구현 클래스는 포트를 괄호에 적는다** (`class InMemoryOrderRepository(OrderRepository):`). Java의 `implements`처럼 어떤 포트의 구현인지 드러나고 IDE에서 구현을 찾을 수 있다.
- **포트의 메서드에는 본문을 넣지 않는다** (`...`만). 본문을 넣으면 구현 클래스가 그 동작을 물려받아 상속이 된다.
- 운영 플랫폼용 구현은 공개 하네스에 없다. 사용자 스킬 폴더의 플랫폼 전용 스킬에 견본이 있으면 그것을 따른다.
- 테스트는 연결 창구 자리에 가짜를 넣는다. 로컬 Redis·PostgreSQL이 꺼져 있어도 테스트는 돈다 (`python-testing`).

```python
# app/application/ports.py
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
| 비어 있음 / `local` | `app/infrastructure/local.py` |
| 그 밖의 값 (예: 운영 플랫폼 이름) | `app/infrastructure/<값>.py` |

- 운영 플랫폼의 `run-application.sh`에 `PLATFORM` 값을 적는다. 로컬에서는 비워 둔다.
- **운영용 구현을 불러오지 못하면 오류를 내고 서버를 멈춘다.** 로컬 구현으로 조용히 바꾸지 않는다 (운영에서 가짜 답이 나가는 사고를 막는다).
- 자동 감지(패키지가 있으면 운영용)는 쓰지 않는다.
- 고르는 곳은 `app/infrastructure/__init__.py`의 `build_platform()` 한 곳이다. `main.py`가 서버 시작 때 한 번 부른다. `local.py`와 `<운영>.py`는 구현들을 모아 묶음(`Platform`)을 만드는 `create_platform()`을 둔다.

```python
def build_platform(settings: Settings | None = None) -> Platform:
    """PLATFORM 환경 변수에 맞는 연결 창구 묶음을 만든다."""
    settings = settings or load_settings()
    name = settings.platform or "local"
    try:
        module = importlib.import_module(f"app.infrastructure.{name}")
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
| 의존성 역전 (DIP) | `application`은 자기 폴더의 Protocol(포트)에만 의존한다. 구현은 `infrastructure`에 있고 바깥에서 넣어 준다 |
| 의존성 주입 | `app/container.py` 한 곳에서 구현을 골라 조립해 넘겨준다 (Spring이 해 주던 일을 직접). 함수 안에서 구현을 직접 만들지 않는다 |
| 캡슐화 | 밖에서 쓰지 않는 것은 `_`로 시작한다. 값 묶음은 `@dataclass(frozen=True)`. 내부 리스트는 복사본이나 `tuple`로 돌려준다 |
| 다형성 | `isinstance` 분기가 반복되면 Protocol 구현을 나눈다 |
| 조합 > 상속 | 기능을 상속으로 물려받지 않고, 필요한 객체를 인자로 받아서 쓴다 |
| 객체 생성 | 검증은 `__post_init__`. 생성자를 바로 불러도 된다. 만드는 상황마다 채우는 값이 다를 때만 `create()`/`restore()` (`python-style`) |

Python에는 `private`, `final`, `new`가 없다. Java 문법을 흉내 내지 않는다 (예: 생성자를 막으려고 `__new__`를 건드리지 않는다).

## DDD — 업무 규칙이 있을 때만

에이전트는 보통 "질문 → LLM 판단 → 도구로 외부 시스템 호출 → 답" 흐름이라 내 코드 안의 업무 규칙이 얇다. 그래서 **계산·판단·상태 변화 같은 규칙이 있을 때만** `app/domain/`을 만든다. 외부 시스템을 불러 주기만 하는 도구뿐이면 만들지 않는다. 이때도 업무 서비스(`app/application/<이름>_service.py`)는 둔다. designer가 설계 문서에 업무 규칙 유무를 적는다.

| DDD 개념 | Python에서 |
|---|---|
| 값 객체 | `@dataclass(frozen=True)` + `__post_init__` 검증 |
| 엔티티 | id를 가진 클래스. 상태는 의미 있는 메서드로만 바꾼다 |
| 애그리거트 | 엔티티 묶음. 바깥은 루트를 통해서만 접근 |
| 리포지토리 | `Protocol`은 `app/application/ports.py`에, 구현은 `app/infrastructure/persistence/`에. 구현은 도메인 객체를 돌려준다 |
| 도메인 서비스 | 한 객체에 넣기 애매한 규칙을 담는 함수 |

`app/domain/`은 LangChain, FastAPI, pydantic 같은 바깥 패키지를 import하지 않는다.
