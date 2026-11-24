---
name: agent-architecture
description: Python AI 에이전트 아키텍처 규칙 — 4계층(presentation / application / domain / infrastructure)과 포트·어댑터 의존 방향, 기능 폴더(유스케이스·Command/Query·Result·서비스·포트)와 도구의 역할, 답 만들기 포트(AnswerGenerator)와 LangGraph 어댑터, 조립(app/container.py), 공통 영역(app/common, 계층별 common)과 공통 예외 위치, 연결 창구(ABC 포트) 구조와 로컬/운영 구현 선택(PLATFORM), LLM과 코드의 역할 나누기, 가드레일 위치, 객체지향(클래스가 기본)·DDD를 Python으로 지키는 법. 에이전트 코드를 구현하거나 리뷰할 때 참조.
---

# Agent Architecture

## 레이어와 의존 방향

4계층에 포트·어댑터를 더한 구조다. Java 하네스(`java:layered-architecture`)와 같은 이름을 쓴다.

```text
main.py ──▶ app/container.py (조립: 구현을 골라 연결)

app/presentation      FastAPI — 엔드포인트, 요청·응답, 전역 예외 핸들러
        │
        ▼
app/application       에이전트 흐름(agent/), 기능별 유스케이스·서비스·포트(<기능>/)
        │                          ▲
        ▼                          │ 포트를 구현 · 서비스를 호출
app/domain            업무 규칙     │
                                   │
app/infrastructure    답 만들기 어댑터(agent/), LLM·저장소·프롬프트·가드레일 구현, 도구(tools/)

app/common/errors.py (공통 예외)  ◀──  모든 레이어
```

| 레이어 | 두는 것 | import할 수 있는 프로젝트 코드 |
|---|---|---|
| `app/presentation` | 엔드포인트, 요청·응답 모델, 공통 응답 틀, 전역 예외 핸들러 | `application`, `app/common/errors.py` |
| `app/application/agent/` | 채팅 기능 — `usecase.py`(`ChatUseCase`), `service.py`(`ChatService`: 입력 검사 → 답 글자 받기 → 문장별 출력 검사, 시간 제한), `command.py`, `port.py`(`AnswerGenerator`·`Guardrail`) | `application` 안, `domain`, `app/common/errors.py` |
| `app/application/<기능>/` | 업무 기능 하나 — `usecase.py`(들어오는 포트), `port.py`(나가는 포트), `service.py`, `command.py`, `result.py` | 같은 기능 폴더, `domain`, `app/common/errors.py` |
| `app/domain/<기능>/` | 도메인 객체(엔티티·값 객체)와 업무 규칙, 코드값 Enum, 업무 예외 | `app/common/errors.py`만 |
| `app/infrastructure` | 포트 구현(어댑터) — 답 만들기(`agent/`), 저장소, 가드레일, 도구. LLM·프롬프트 창구(`llm/`, `prompt/`)와 그 모양(`port.py`), 설정, 구현 선택 | `application`, `domain`, `app/common/errors.py` |
| `app/container.py` | 조립 — 구현을 서비스·도구·에이전트에 넣어 주기 | 전부 |
| `main.py` | 부트스트랩 — `FastAPI` 앱 만들기, `lifespan`에서 조립(`Container`) 부르기, 전역 예외 핸들러 등록 | 전부 |
| `app/common/` | 모든 계층이 쓰는 것 — `errors.py`(공통 예외) | 표준 라이브러리만 |
| `app/application/common/` | 애플리케이션 안 여러 기능이 쓰는 도우미 — `time_limit.py`(`TimeLimit`), `sentences.py`(`SentenceSplitter`) | `app/common/`, 표준 라이브러리 |

- **`application`과 `domain`은 `infrastructure`와 `presentation`을 import하지 않는다.** 위반이면 불통과다.
- `presentation`은 `infrastructure`를 import하지 않는다. 필요한 것은 `container.py`가 만들어 `app.state`에 둔다.
- **구현을 골라 끼우는 곳은 `container.py`(와 그것을 부르는 `main.py`)뿐이다.** 서비스 구현(`OrderService`, `ChatService`)과 어댑터 구현을 만들어 서로 넣어 주는 일은 여기서만 한다. `infrastructure`는 `application`의 포트·유스케이스·DTO를 import할 수 있지만 서비스 구현을 만들지 않는다.
- `application`, `domain`에서 운영 플랫폼 SDK를 import하거나 `os.environ`을 읽으면 위반이다.

### 공통 영역

"공통"은 누가 쓰느냐에 따라 두 단계로 나눈다. 기능 폴더(`agent/`, `<기능>/`)에는 **그 기능의 규칙이나 결정이 들어 있는 것**을 둔다.

| 단계 | 둘 곳 | 지금 있는 것 | 조건 |
|---|---|---|---|
| 모든 계층이 쓰는 것 | `app/common/` | `errors.py` | 표준 라이브러리만 쓴다. `domain`도 import할 수 있으므로 기술(asyncio, FastAPI 등)을 넣지 않는다 |
| 한 계층 안에서, 기능의 규칙·결정 없이 쓸 수 있는 기술 도우미 | 그 계층의 `common/` (presentation은 `response/`) | `application/common/time_limit.py`, `application/common/sentences.py`, `presentation/response/sse_response.py` | 그 계층의 규칙(쓸 수 있는 패키지)을 따른다 |

- **나누는 기준은 "기능의 규칙이나 결정이 들어 있느냐"다.** 시간 제한 걸기, 조각을 문장으로 모으기처럼 채팅·주문을 몰라도 쓸 수 있는 기술은 지금 한 기능만 써도 `common/`에 둔다. 주문 도구가 결제 시각을 어떤 모양으로 보여 줄지처럼 기능의 결정이 들어 있으면 기능 폴더에 둔다.
- 기능 폴더끼리 서로 import하지 않는다. 두 기능이 같이 쓸 것이 생기면 기능의 결정을 떼어 내고 그 계층의 `common/`으로 옮긴다.
- **폴더 이름은 위치를, 파일 이름은 하는 일을 말한다.** 공유 자리는 어느 계층이든 `common/`이라고 부른다. `common/` 안은 기술 하나당 파일 하나로, 하는 일로 이름 붙인다 (`time_limit.py`, `sentences.py`). `util`·`utils`·`helpers`처럼 무엇이 들어 있는지 말하지 않는 이름의 폴더·파일을 만들지 않는다.
- 에이전트가 여럿이 되면 `app/<에이전트>/` 아래에 계층을 두고 공통은 `app/common/<계층>/`로 옮긴다. 그때 구조는 사용자와 정한다.

### 바깥 패키지를 쓸 수 있는 곳

| 패키지 | 쓸 수 있는 곳 |
|---|---|
| FastAPI | `main.py`, `app/presentation` |
| LangChain·LangGraph | `app/infrastructure` |
| 운영 플랫폼 SDK, DB·Redis 클라이언트 | `app/infrastructure` |
| `pydantic-settings` (환경 변수 읽기) | `app/infrastructure/settings.py` |
| 없음 (표준 라이브러리만) | `app/domain`, `app/application` |

LangChain·LangGraph는 프레임워크라 바깥(`infrastructure`)에만 둔다. `application`은 답을 글자로만 주고받는다 (아래 "답 만들기"). 그래서 프레임워크를 바꾸거나 LLM이 답을 보내는 방식이 달라져도 `application`과 `domain`은 그대로다.

## Command — presentation에서 application으로 넘기는 값

`presentation`은 요청 모델을 그대로 넘기지 않고 Command로 바꿔 넘긴다. Java 하네스의 Command와 같은 역할이다.

```python
# app/application/agent/command.py
@dataclass(frozen=True)
class ChatCommand:
    """에이전트에 넘기는 질문 한 건."""

    conversation_id: str
    message: str


# app/presentation/routes.py
command = ChatCommand(conversation_id=body.conversation_id, message=body.message)
```

- Command는 `app/application`에 두는 변하지 않는 값 묶음이다 (`@dataclass(frozen=True)`). pydantic을 쓰지 않는다. 형식 검사는 요청 모델이 이미 했다.
- `application`은 요청 모델(`ChatRequest`)을 모른다. 넘길 값이 늘면 Command에 칸을 더하고 메서드 모양은 그대로 둔다.
- 바꾸는 곳은 `app/presentation/routes.py`다.
- 기능의 유스케이스가 받는 값(`GetOrderQuery`, `CancelOrderCommand`)도 같은 규칙이다 (아래 "기능 폴더").

## 기능 폴더 — 유스케이스, 서비스, 도구

업무 기능 하나(주문, 상품 등)는 폴더 하나다. Java 하네스·Kotlin 프로젝트의 `application/<기능>/`과 같은 모양이다. 도구는 LLM이 시스템을 부르는 창구라서, 도구 안에 업무 순서를 적지 않고 **항상 유스케이스를 거친다.**

```text
app/domain/order/order.py                엔티티(Order), 코드값 Enum, 취소 규칙, 업무 예외
app/application/order/
├── usecase.py   OrderUseCase       들어오는 포트 — 이 기능이 바깥에 제공하는 일의 목록
├── port.py      OrderRepository    나가는 포트 — 이 기능이 바깥에 요구하는 것
├── service.py   OrderService(OrderUseCase)
├── command.py   GetOrderQuery, CancelOrderCommand
└── result.py    OrderResult
app/infrastructure/persistence/order/    OrderRepository 구현
app/infrastructure/tools/order_tools.py  OrderUseCase를 받아 결과를 문장으로
```

| 파일 | 맡는 일 | 모르는 것 |
|---|---|---|
| `app/domain/<기능>/` | 도메인 객체와 판단·계산 (예: 취소할 수 있는가). 규칙이 없으면 값만 갖는다 | 저장소, LLM, 문장 |
| `app/application/<기능>/service.py` | 순서 (꺼내기 → 도메인에 판단 맡기기 → 저장). 결과는 Result나 업무 예외로 알린다 | LangChain, LLM이 읽을 문장 |
| `app/infrastructure/tools/` | 유스케이스 호출, Result와 예외를 LLM이 읽을 문장으로 바꾸기 | 판단, 순서, 엔티티, 서비스 구현 |

```python
# app/application/order/command.py
@dataclass(frozen=True)
class GetOrderQuery:
    order_id: str

@dataclass(frozen=True)
class CancelOrderCommand:
    order_id: str

# app/application/order/result.py
@dataclass(frozen=True)
class OrderResult:
    order_id: str
    status: OrderStatus          # 도메인의 코드값 Enum은 그대로 쓴다
    paid_at: datetime

    @classmethod
    def from_order(cls, order: Order) -> "OrderResult":
        return cls(order_id=order.order_id, status=order.status, paid_at=order.paid_at)

# app/application/order/usecase.py
class OrderUseCase(ABC):
    @abstractmethod
    async def get_order(self, query: GetOrderQuery) -> OrderResult: ...

    @abstractmethod
    async def cancel_order(self, command: CancelOrderCommand) -> OrderResult: ...

# app/application/order/port.py
class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime: ...              # 구현: infrastructure/clock/system_clock.py

# app/application/order/service.py
class OrderService(OrderUseCase):
    def __init__(self, orders: OrderRepository, clock: Clock) -> None:
        self._orders = orders
        self._clock = clock

    @override
    async def cancel_order(self, command: CancelOrderCommand) -> OrderResult:
        order = await self._find_order(command.order_id)
        cancelled = order.cancel(self._clock.now())  # 판단은 도메인
        await self._orders.save(cancelled)
        return OrderResult.from_order(cancelled)    # 엔티티를 밖으로 내보내지 않는다

    async def _find_order(self, order_id: str) -> Order:
        order = await self._orders.find(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order
```

- **유스케이스(`usecase.py`)는 `ABC`이고 모든 메서드에 `@abstractmethod`를 붙인다. 본문은 넣지 않는다.** 서비스는 `class OrderService(OrderUseCase):`로 구현임을 적고, 유스케이스 메서드를 구현한 메서드에 `@override`를 붙인다.
- **유스케이스 메서드는 Command/Query를 받고 Result를 돌려준다.** 상태를 바꾸지 않는 요청은 `...Query`, 바꾸는 요청은 `...Command`로 이름 붙이고 둘 다 `command.py` 한 파일에 둔다. 셋 다 `@dataclass(frozen=True)`이고 pydantic을 쓰지 않는다.
- **DTO(Command·Query·Result)는 그 기능 폴더의 `command.py`·`result.py`에 둔다.** 채팅 기능도 `agent/command.py`다. 모든 기능의 DTO를 모으는 폴더(`application/dto/` 등)를 따로 만들지 않는다. 한 기능의 Command가 많아 파일이 길어지면 `command.py`를 `command/` 패키지로 바꾼다.
- **서비스는 엔티티를 밖으로 돌려주지 않는다.** Result로 옮겨 담아 돌려준다. Result에는 부르는 쪽이 필요한 값만 담는다. 도메인의 코드값 Enum은 그대로 써도 되고, 엔티티는 담지 않는다. 엔티티가 바뀌어도 옮겨 담는 곳(서비스·`from_<엔티티>`)에서 멈추고 도구까지 번지지 않는다.
- **대상이 없을 때: 저장소(나가는 포트)는 `None`을 돌려주고, 서비스가 업무 예외(`OrderNotFoundError`)로 바꿔 던진다.** 유스케이스의 반환 타입에 `None`을 넣지 않는다. 예외에는 대상 값만 넘긴다 (`raise OrderNotFoundError(order_id)`). 메시지는 예외가 만든다 (아래 "예외 위치").
- **도구는 유스케이스를 통해서만 기능을 쓴다.** 도구가 import할 수 있는 것은 아래 표가 전부다.

| import할 수 있다 | import하지 않는다 |
|---|---|
| 유스케이스(`OrderUseCase`), 그 기능의 Command·Query(`command.py`)·Result(`result.py`) | 서비스 구현(`OrderService`) |
| 도메인의 코드값 Enum(`OrderStatus`), 업무 예외(`OrderNotFoundError`) | 엔티티(`Order`), 나가는 포트(`OrderRepository`) |
- **포트는 그것을 쓰는 폴더에 둔다.** 기능의 나가는 포트는 `application/<기능>/port.py`, 답 흐름이 쓰는 `AnswerGenerator`·`Guardrail`은 `application/agent/port.py`. LLM·프롬프트 창구는 답 만들기 어댑터와 조립만 쓰므로 `infrastructure/llm/port.py`, `infrastructure/prompt/port.py`에 둔다. 모든 포트를 한 파일에 모으지 않는다.
- **도메인은 코드값만 갖고, 사용자에게 보이는 이름과 문장은 도구가 갖는다.** 상태·사유 같은 Enum의 값은 코드(`PAID`, `SHIPPING_STARTED`)로 두고, 표시용 이름("결제 완료")과 안내 문장은 도구의 표(`STATUS_LABELS`, `CANCEL_DENIAL_SENTENCES`)에 둔다. 문구를 바꿔도 도메인과 저장된 값은 그대로다.

```python
# app/domain/order/order.py
class OrderStatus(StrEnum):
    PAID = "PAID"
    SHIPPING = "SHIPPING"

# app/infrastructure/tools/order_tools.py
STATUS_LABELS: dict[OrderStatus, str] = {
    OrderStatus.PAID: "결제 완료",
    OrderStatus.SHIPPING: "배송 중",
}
```

- 날짜·시각을 읽기 좋은 표기로 바꾸는 것(시간대, 날짜 형식)도 문장 만들기로 보고 도구가 한다.
- 조회처럼 전달만 하는 기능도 유스케이스를 거친다. 서비스가 한 줄이어도 도구가 포트를 직접 부르지 않는다. 기준이 하나여야 도구마다 판단이 갈리지 않는다.
- 서비스는 나가는 포트를 생성자로 받는다. "지금 시각"도 시계 포트(`Clock`)로 받는다. 안에서 시계를 읽거나 구현을 만들지 않는다. 함수(`now: Callable`)를 넘기지 않는다.
- 도구가 예외를 문장으로 바꾸는 규칙은 `langgraph-conventions`의 "도구 만들기"를 따른다. **문장으로 바꾸는 것은 업무 예외(대상 없음, 규칙에 걸림)뿐이다.** 포트 구현이 외부 시스템(DB, 외부 API) 고장으로 던지는 `UpstreamError`는 도구가 잡지 않는다. 그대로 올라가 `UPSTREAM_ERROR`로 끝난다 (Fail Fast). 고장을 문장으로 바꾸면 LLM이 그 문장을 보고 답을 지어낼 수 있다.

## 채팅 기능 — ChatUseCase와 ChatService

에이전트에 질문하고 답을 받는 일도 업무 기능처럼 **유스케이스 + 서비스**로 둔다. 주문 기능과 모양이 같다.

```python
# app/application/agent/usecase.py
class ChatUseCase(ABC):
    @abstractmethod
    def stream_answer(self, command: ChatCommand) -> AsyncIterator[str]: ...

# app/application/agent/service.py
class ChatService(ChatUseCase):
    def __init__(self, answers: AnswerGenerator, guardrail: Guardrail, time_limit: TimeLimit) -> None:
        self._answers = answers
        self._guardrail = guardrail
        self._time_limit = time_limit
        self._sentences = SentenceSplitter()            # 설정도 구현도 하나뿐인 도우미

    @override
    def stream_answer(self, command: ChatCommand) -> AsyncIterator[str]:
        sentences = self._checked_sentences(command)
        return self._time_limit.apply(sentences)

    async def _checked_sentences(self, command: ChatCommand) -> AsyncGenerator[str]:
        checked = await self._guardrail.check_input(command.message)
        if checked.blocked:
            raise InputBlockedError(checked.message)    # 안내 문구는 SseResponse가 보낸다
        async for sentence in self._sentences.split(self._answers.stream(checked.text)):
            yield await self._check_output(sentence)

    async def _check_output(self, sentence: str) -> str:
        checked = await self._guardrail.check_output(sentence)
        if checked.blocked:
            raise OutputBlockedError(checked.message)   # 막힌 문장은 내보내지 않는다
        return checked.text                             # 가려졌을 수 있는 문장
```

- **서비스의 공개 메서드는 업무 단계만 적는다.** `OrderService.cancel_order`(꺼내기 → 판단 맡기기 → 저장 → 결과)처럼 몇 줄로 읽혀야 한다. 시간 제한(`TimeLimit`), 글자 조각을 문장으로 모으기(`SentenceSplitter`) 같은 기술은 클래스로 빼고 메서드 이름으로 부른다. 둘 다 뼈대의 `app/application/common/`에 있다.
- 서비스가 쓰는 부품(답 만들기 창구, 가드레일, 시간 제한)은 생성자로 받아 필드로 둔다. 부품을 따로 묶은 값(`AgentContext` 같은 것)을 만들어 메서드에 넘기지 않는다.
- 설정 값도 바꿔 끼울 구현도 없는 도우미(`SentenceSplitter`)는 받지 않고 생성자 안에서 만든다. 설정 값이 있는 `TimeLimit`은 `Container`가 만들어 넣는다.
- `/chat`은 `ChatUseCase`에만 의존한다. 조립(`Container`)이 만든 서비스를 `app.state.chat`에 두고 꺼내 쓴다.
- Command(`ChatCommand`)는 요청마다 새로 만드는 값(DTO)이고, 서비스는 서버 시작 때 한 번 만드는 객체다.

## 답 만들기 — AnswerGenerator 포트와 LangGraph 어댑터

채팅 서비스(`application/agent/service.py`)는 LLM·LangGraph를 모르고 **답 글자만** 받는다. LangGraph로 에이전트를 돌리고 그 메시지를 글자로 바꾸는 일은 어댑터가 한다.

```python
# app/application/agent/port.py — 포트: 프레임워크 모양을 드러내지 않는다
class AnswerGenerator(ABC):
    @abstractmethod
    def stream(self, question: str) -> AsyncIterator[str]: ...

# app/infrastructure/agent/langgraph_answer_generator.py — 어댑터 (뼈대에 있다)
class LangGraphAnswerGenerator(AnswerGenerator):
    def __init__(self, model: BaseChatModel, tools: Sequence[BaseTool], system_prompt: str) -> None:
        self._agent = create_agent(..., middleware=[UpstreamErrorMiddleware()])

    @override
    async def stream(self, question: str) -> AsyncIterator[str]:
        async for message, _ in self._agent.astream(..., stream_mode="messages"):
            text = self._answer_text(message)  # 조각이든 완성된 답이든 글자만
            if text:
                yield text

# app/application/agent/service.py — 채팅 서비스: 글자만 받는다
async for text in self._answers.stream(checked.text):
    ...                                        # 문장 나누기, 출력 검사, 시간 제한
```

| 어댑터가 바꾸는 것 | 바깥 모양 | 우리 모양 |
|---|---|---|
| 질문 | `HumanMessage` | `str` |
| 답 | `AIMessageChunk`(조각으로 보내는 LLM) 또는 `AIMessage`(한 번에 보내는 LLM) | 글자 조각 `str` |
| 도구 호출·도구 결과 | `AIMessage(tool_calls=...)`, `ToolMessage` | 내보내지 않음 |
| LLM 호출 실패 | LLM 라이브러리의 예외 | `UpstreamError` |

- **어댑터는 조각(`AIMessageChunk`)과 완성된 답(`AIMessage`)을 둘 다 받는다.** LLM이 조각 보내기를 지원하지 않거나 꺼져 있으면 완성된 답 하나만 온다. 조각만 받으면 이때 빈 답이 나간다.
- 뼈대의 `LangGraphAnswerGenerator`를 그대로 쓴다. 새로 만들지 않는다. `StateGraph`로 만드는 에이전트는 같은 `AnswerGenerator`를 구현하는 어댑터를 `infrastructure/agent/`에 더한다.
- `application`에서 LangChain·LangGraph를 import하면 위반이다.

## 조립 (app/container.py)

```python
class Container:
    """연결 창구 묶음과 설정으로 서비스를 조립한다. 서버 시작 때 한 번 만든다."""

    def __init__(self, platform: Platform, settings: Settings) -> None:
        self._platform = platform
        self._settings = settings

    def build_chat_service(self) -> ChatUseCase:
        platform = self._platform
        orders = OrderService(platform.orders, SystemClock())
        answers = LangGraphAnswerGenerator(
            model=platform.llm.chat_model(),
            tools=OrderTools(orders).build(),          # 도구에는 OrderUseCase로 넘어간다
            system_prompt=platform.prompts.get("system"),
        )
        time_limit = TimeLimit(self._settings.agent_timeout_seconds)
        return ChatService(answers, platform.guardrail, time_limit)
```

- 구현 → 기능 서비스 → 도구 → 답 만들기 어댑터 → 채팅 서비스 순서로 넣어 준다. 돌려주는 타입은 유스케이스(`ChatUseCase`)다. 서비스 구현을 아는 곳은 `container.py`의 `Container`뿐이다.
- 만드는 서비스가 늘면 `build_<서비스>()` 메서드를 더한다. 조립 클래스를 따로 만들지 않는다.
- `main.py`의 `lifespan`이 `Settings()`로 설정을, `Platform.from_settings()`로 구현 묶음을 만들고 `Container(platform, settings).build_chat_service()` 결과를 `app.state`에 둔다.
- 테스트는 가짜 구현 묶음을 같은 `Container`에 넣는다. 테스트용 조립 코드를 따로 만들지 않는다.

## 예외 위치

예외는 던진 곳에서 호출한 쪽으로 올라가고, 아무도 잡지 않으면 FastAPI가 잡아 전역 핸들러에 넘긴다. 그래서 던지는 쪽과 응답으로 바꾸는 쪽을 나눈다.

| 무엇 | 위치 | 이유 |
|---|---|---|
| 여러 레이어가 던지거나 전역 핸들러가 구분해 답하는 예외 (`AppError`, `UpstreamError`, `AgentTimeoutError`) | `app/common/errors.py` | 안쪽 레이어가 import해야 하므로 HTTP를 몰라야 한다 |
| 한 레이어 안에서만 쓰는 예외 (예: `PlatformLoadError`) | 그 레이어 안 | 밖에서 구분할 일이 없다 |
| 업무 예외 — 대상이 없을 때(`OrderNotFoundError`), 업무 규칙에 걸렸을 때(`OrderNotCancellableError`) | `app/domain/<기능>/` (도메인 객체 옆) | 도구가 잡아 문장으로 바꾼다. 전역 핸들러까지 가지 않는다 |
| 외부 시스템(DB, 외부 API) 고장 | 포트 구현이 `UpstreamError`(`app/common/errors.py`)를 던진다 | 도구가 잡지 않는다. `UPSTREAM_ERROR`로 끝난다 |
| 가드레일에 막혔을 때 던지는 예외 (`InputBlockedError`, `OutputBlockedError`) | `app/application/agent/errors.py` (뼈대) | `SseResponse`가 잡아 입력 막힘은 안내 문구 답으로, 출력 막힘은 `BLOCKED` 이벤트로 바꾼다. 전역 핸들러까지 가지 않는다 |
| 예외 → 상태 코드·`code`·안내 문구 대응표, 전역 핸들러 | `app/presentation/exception/` (`ErrorRuleBook`, `GlobalExceptionHandler`) | HTTP 응답을 만드는 일이다 (`fastapi-conventions`) |
| `code` 값(`ErrorCode`), 안내 문구 | `app/presentation/response/` | 호출하는 쪽에 보이는 응답의 일부다 |

- 예외 클래스에 상태 코드나 `code`를 넣지 않는다. 대응은 `ErrorRuleBook`(`app/presentation/exception/error_rule.py`)의 표 한 곳에만 둔다.
- **업무 예외는 대상 값을 생성자로 받아 메시지를 스스로 만든다.** 던지는 쪽은 값만 넘긴다. 문구가 예외 한 곳에만 있어 던지는 곳마다 달라지지 않고, 잡는 쪽은 값(`e.order_id`)을 속성으로 쓴다.

```python
# app/domain/order/order.py
class OrderNotFoundError(AppError):
    """주문 번호에 해당하는 주문이 없을 때.

    Attributes:
        order_id: 찾지 못한 주문 번호.
    """

    def __init__(self, order_id: str) -> None:
        super().__init__(f"주문을 찾을 수 없다: order_id={order_id}")
        self.order_id = order_id
```

- 새 예외는 `AppError`나 그 하위 예외를 상속한다. 대응표에 없으면 가장 가까운 부모의 규칙으로 답한다.
- **의도된 결과라도 흐름을 끝내는 것은 예외로 던지고, 가까운 곳에서 이름을 적어 잡는다** (취소 불가는 도구가, 입력·출력 막힘은 `SseResponse`가). 값에 표시를 달아 넘기면 받는 쪽이 확인을 빠뜨려도 조용히 지나간다. 이런 예외는 오류가 아니므로 대응표(`ErrorRuleBook`)에 넣지 않는다. 잡는 곳을 빠뜨리면 `INTERNAL_ERROR`로 드러난다.

## 연결 창구 — 포트와 구현

바깥 시스템에 닿는 일은 모두 연결 창구를 거친다. 창구 하나는 포트(`ABC`) 하나다. 모양(포트)은 그것을 쓰는 폴더(기능은 `app/application/<기능>/port.py`, 답 흐름은 `app/application/agent/port.py`, 답 만들기 어댑터가 쓰는 LLM·프롬프트는 `app/infrastructure/llm/port.py`·`prompt/port.py`)에, 구현(어댑터)은 `app/infrastructure/`에 둔다.

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
- 구현은 창구 종류마다 폴더 하나에 둔다: `infrastructure/agent/`, `llm/`, `persistence/<기능>/`(DB·메모리 저장소), `client/<기능>/`(외부 API를 부르는 구현), `prompt/`, `guardrail/`. 도구는 `infrastructure/tools/`.
- **업무 기능의 나가는 포트(저장소, 외부 API)도 연결 창구다.** 기능이 생기면 `Platform`(`app/infrastructure/__init__.py`)에 칸을 더하고(예: `orders: OrderRepository`), 같은 변경에서 `local.py`의 `LocalPlatformFactory`와 `tests/fakes.py`의 `fake_platform`도 고친다. `Container`는 `platform.orders`처럼 꺼내 서비스에 넣는다.
- **포트는 `abc.ABC`를 상속하고 모든 메서드에 `@abstractmethod`를 붙인다.** Java의 `interface` 역할이다. 구현 클래스가 메서드를 빠뜨리면 객체를 만들 때 `TypeError`가 난다.
- **구현 클래스는 포트를 괄호에 적어 상속한다** (`class InMemoryOrderRepository(OrderRepository):`). Java의 `implements`처럼 어떤 포트의 구현인지 드러나고 IDE에서 구현을 찾을 수 있다. 상속하지 않으면 메서드 모양이 같아도 타입 검사에 걸린다. 테스트용 가짜 클래스도 포트를 상속한다.
- **포트 메서드를 구현한 메서드에는 `@override`를 붙인다** (`from typing_extensions import override`). Java의 `@Override` 역할이다. 어떤 메서드가 포트의 구현인지 드러나고, 포트에서 이름이 바뀌거나 없어진 메서드가 구현에 남으면 타입 검사에 걸린다. 테스트용 가짜 클래스도 같다 (`python-style`의 "타입 표시").
- **포트에는 추상 메서드만 둔다.** 본문은 `...`만 적는다. 필드, `__init__`, 본문이 있는 메서드를 넣지 않는다. 넣으면 구현 클래스가 그 동작을 물려받아 기능 상속이 된다.
- 운영 플랫폼용 구현은 공개 하네스에 없다. 사용자 스킬 폴더의 플랫폼 전용 스킬에 견본이 있으면 그것을 따른다.
- 테스트는 연결 창구 자리에 가짜를 넣는다. 로컬 Redis·PostgreSQL이 꺼져 있어도 테스트는 돈다 (`python-testing`).

```python
# app/application/agent/port.py
class ConversationMemory(ABC):
    """대화 id별 최근 대화를 일정 시간 기억하는 창구."""

    @abstractmethod
    async def load(self, conversation_id: str) -> list[BaseMessage]:
        """저장된 최근 대화를 돌려준다. 없거나 만료됐으면 빈 목록."""
        ...

    @abstractmethod
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
- 고르는 곳은 `app/infrastructure/__init__.py`의 `Platform.from_settings()` 한 곳이다. `main.py`가 서버 시작 때 한 번 부른다.
- `local.py`와 `<운영>.py`는 구현들을 모아 묶음(`Platform`)을 만드는 클래스(`PlatformFactory` 구현)를 두고, 그 인스턴스를 모듈의 `factory` 이름으로 내놓는다. `from_settings()`가 이 이름으로 찾는다.

```python
# app/infrastructure/__init__.py
@dataclass(frozen=True)
class Platform:
    ...

    @classmethod
    def from_settings(cls, settings: Settings) -> "Platform":
        """PLATFORM 값에 맞는 구현 모듈의 factory로 연결 창구 묶음을 만든다."""
        name = settings.platform or LOCAL
        try:
            module = importlib.import_module(f"app.infrastructure.{name}")
        except ImportError as e:
            raise PlatformLoadError(f"연결 창구를 불러오지 못했다: PLATFORM={name}") from e
        factory: PlatformFactory = module.factory
        return factory.create(settings)

# app/infrastructure/local.py
class LocalPlatformFactory(PlatformFactory):
    @override
    def create(self, settings: Settings) -> Platform:
        return Platform(llm=OpenAiCompatibleLlm(settings), ...)

factory = LocalPlatformFactory()
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
| 추상화 (인터페이스) | `abc.ABC`와 `@abstractmethod`로 포트를 정한다 (Java `interface` 역할). 구현 클래스는 포트를 상속하고 (Java `implements` 역할), 구현한 메서드에 `@override`를 붙인다 (Java `@Override` 역할) |
| 의존성 역전 (DIP) | `application`은 자기 폴더의 포트(ABC)에만 의존한다. 구현은 `infrastructure`에 있고 바깥에서 넣어 준다 |
| 클래스가 기본 | 기능은 책임을 가진 클래스로 만든다. 모듈 함수는 프레임워크가 함수를 요구하는 곳만 쓴다 (`python-style`의 "클래스가 기본") |
| 의존성 주입 | `app/container.py`의 `Container` 한 곳에서 구현을 골라 조립해 넘겨준다 (Spring이 해 주던 일을 직접). 클래스 안에서 구현을 직접 만들지 않는다. 설정 값도 바꿔 끼울 구현도 없는 도우미만 생성자 안에서 만든다 |
| 캡슐화 | 밖에서 쓰지 않는 것은 `_`로 시작한다. 값 묶음은 `@dataclass(frozen=True)`. 내부 리스트는 복사본이나 `tuple`로 돌려준다 |
| 다형성 | `isinstance` 분기가 반복되면 포트 구현을 나눈다 |
| 조합 > 상속 | 기능을 상속으로 물려받지 않고, 필요한 객체를 인자로 받아서 쓴다. 포트 상속은 추상 메서드만 물려받으므로 기능 상속이 아니다 |
| 객체 생성 | 검증은 `__post_init__`. 생성자를 바로 불러도 된다. 만드는 상황마다 채우는 값이 다를 때만 `create()`/`restore()` (`python-style`) |

Python에는 `private`, `final`, `new`가 없다. Java 문법을 흉내 내지 않는다 (예: 생성자를 막으려고 `__new__`를 건드리지 않는다).

## DDD — 업무 규칙이 없어도 도메인 객체를 둔다

**기능의 나가는 포트(저장소, 외부 API)가 업무 데이터를 주고받으면, 업무 규칙이 없어도 `app/domain/<기능>/`에 도메인 객체와 업무 예외를 둔다.** 규칙이 없으면 값만 갖는 `@dataclass(frozen=True)` 클래스다 (예: 조회만 하는 상품의 `Product`). 포트는 늘 도메인 객체를 돌려주고, 서비스가 Result로 옮겨 담는다.

- 그래서 기능마다 폴더 모양(`domain/<기능>/`, `application/<기능>/`, 구현 폴더)이 같다. 규칙이 생기면 그 클래스에 메서드를 더하면 되고, 포트와 서비스의 모양은 그대로다.
- 계산·판단·상태 변화 같은 규칙은 도메인 객체의 메서드로 둔다. 도구나 서비스에 두지 않는다.
- designer가 설계 문서에 도메인 객체와 업무 규칙 유무를 적는다.

| DDD 개념 | Python에서 |
|---|---|
| 값 객체 | `@dataclass(frozen=True)` + `__post_init__` 검증 |
| 엔티티 | id를 가진 클래스. 상태는 의미 있는 메서드로만 바꾼다 |
| 애그리거트 | 엔티티 묶음. 바깥은 루트를 통해서만 접근 |
| 리포지토리 | 포트(`ABC`)는 `app/application/<기능>/port.py`에, 구현은 `app/infrastructure/persistence/<기능>/`에. 구현은 도메인 객체를 돌려주고, 서비스가 Result로 옮겨 담는다 |
| 도메인 서비스 | 한 객체에 넣기 애매한 규칙을 담는 클래스 (예: `RefundPolicy`). 상태가 없어도 클래스로 둔다 |

`app/domain/`은 LangChain, FastAPI, pydantic 같은 바깥 패키지를 import하지 않는다. 기능마다 `app/domain/<기능>/` 폴더를 둔다.
