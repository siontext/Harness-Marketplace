---
name: langgraph-conventions
description: LangChain 1.x / LangGraph 1.x로 에이전트를 만드는 규칙 — create_agent와 StateGraph 고르기(LLM 도구 호출 미지원 시 포함), 도구 클래스(<기능>Tools)와 tool() 감싸기, 미들웨어 클래스, 구조화 출력, 가드레일·대화 기억 연결, 스트리밍, MCP 도구, 사람 확인(HITL), 쓰지 않는 예전 API. 에이전트 흐름·도구 코드를 작성하거나 리뷰할 때 참조.
---

# LangGraph / LangChain Conventions

LangChain 1.x, LangGraph 1.x 기준이다 (확인한 버전: langchain 1.5, langchain-core 1.8, langgraph 1.2). 설치된 버전이 다르면 아래 예시를 그대로 믿지 말고 설치된 패키지 소스를 확인한다. LangChain은 1.0에서 에이전트 만드는 방법이 크게 바뀌었다. **예전 방식(맨 아래 표)으로 짜지 않는다.**

## 에이전트 만드는 방법 고르기

| 방식 | 동작 | 언제 |
|---|---|---|
| `StateGraph` | 순서를 코드로 고정한다 (예: 분류 → 검색 → 답변) | 순서가 정해진 일, 반드시 지켜야 할 순서가 있을 때, LLM이 건너뛰면 안 되는 단계가 있을 때 |
| `create_agent` | LLM이 도구를 알아서 골라 쓰고, 다 됐다고 판단하면 답한다 | 질문마다 필요한 도구와 순서가 달라 코드로 미리 정할 수 없을 때 |

- 어느 쪽도 기본값이 아니다. **순서를 코드로 정할 수 있으면 `StateGraph`를 먼저 검토한다.** LLM이 길을 고르면 지연 시간과 비용이 늘고, 같은 질문에도 다른 길로 갈 수 있다.
- designer가 설계 문서 개요의 "흐름 방식"에 어느 쪽인지와 고른 이유를 적는다.

### LLM이 도구 호출을 지원하지 않을 때

`create_agent`는 LLM의 **도구 호출(tool calling)** 기능이 있어야 동작한다. 모델이나 LLM 게이트웨이 설정에 따라 이 기능이 없을 수 있다.

| 도구 호출 | 기본 방식 |
|---|---|
| 지원함 | `create_agent` |
| 지원하지 않음 / 확인 전 | `StateGraph` — LLM은 구조화 출력으로 "어떤 도구가 필요한지"만 고르고, 도구 실행은 코드 노드가 한다 |

- 지원 여부를 모르면 추측하지 않고 사용자에게 확인한다. **확인 전이면 기본은 `StateGraph`다.** 사용자가 그래도 `create_agent`를 고르면 설계 문서 결정 섹션에 "도구 호출 확인 전"과 고른 이유를 적는다. `/python:eval`의 연결 확인에서 지원하지 않는다고 나오면 `StateGraph` 어댑터로 바꾼다.
- 지원 여부는 `/python:eval`의 연결 확인 단계에서 도구 하나를 붙여 실제로 불러 보면 알 수 있다.

```python
agent = create_agent(
    model=llm,
    tools=[get_product, search_products],
    system_prompt=prompts.get("product_agent"),
)
result = await agent.ainvoke({"messages": messages})
```

- `create_agent`는 `from langchain.agents import create_agent`.
- 에이전트는 답 만들기 어댑터(`app/infrastructure/agent/langgraph_answer_adapter.py`, 뼈대에 있다)가 만든다. LLM·프롬프트·도구는 생성자로 받는다 (`agent-architecture`의 "답 만들기"). `application`은 LangChain·LangGraph를 import하지 않는다.

### LLM 호출 실패 → UpstreamError

LLM 호출이 실패하면 LLM 라이브러리의 예외가 올라온다. 그대로 두면 `INTERNAL_ERROR`로 나가므로, **답 만들기 어댑터에서 모델 호출만 감싸 `UpstreamError`로 바꾼다.** 뼈대의 어댑터에 들어 있다.

```python
class UpstreamErrorMiddleware(AgentMiddleware):
    """LLM 호출 실패를 UpstreamError로 바꿔 던진다. 도구 실행은 감싸지 않는다."""

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        try:
            return await handler(request)
        # LLM 구현마다 던지는 예외가 달라 타입을 좁힐 수 없다.
        except Exception as e:
            raise UpstreamError.llm_call_failed(type(e).__name__) from e


agent = create_agent(..., middleware=[UpstreamErrorMiddleware()])
```

- `AgentMiddleware`, `ModelRequest`, `ModelResponse`는 `from langchain.agents.middleware import ...`.
- **미들웨어는 `AgentMiddleware`를 상속한 클래스로 만든다.** 함수에 붙이는 데코레이터(`@wrap_model_call`, `@before_model`, `@after_model`)는 쓰지 않는다 (`python-style`의 "클래스가 기본"). 에이전트를 `astream`·`ainvoke`로 돌리므로 `a`로 시작하는 메서드(`awrap_model_call`, `abefore_model`, `aafter_model`)를 구현한다.
- 모델 호출만 감싼다. 도구 실행까지 감싸면 도구 안의 코드 버그가 `UpstreamError`로 바뀌어 가려진다.
- 예외 메시지에는 예외 종류만 넣는다. LLM 라이브러리의 메시지에는 주소나 키 일부가 들어 있을 수 있다. 원인은 `from e`로 잇고 로그에서 본다.
- `StateGraph`로 만들 때는 LLM을 부르는 노드에서 같은 방식으로 바꾼다. 노드는 어댑터 클래스의 메서드로 두고 `graph.add_node("<이름>", self._<노드>)`로 붙인다.
- 필수 테스트: LLM 호출 실패가 `UPSTREAM_ERROR`로 나가는지, 도구의 코드 버그는 `UPSTREAM_ERROR`로 바뀌지 않는지.

## 도구 만들기

도구는 `app/infrastructure/tools/`에 둔다. 도구는 유스케이스를 부르고 결과(Result)를 LLM이 읽을 문장으로 바꾸는 일만 한다 (`agent-architecture`의 "기능 폴더").

- **도구는 `<기능>Tools` 클래스의 공개 메서드로 만든다.** 클래스는 유스케이스를 생성자로 받고, `build()`가 메서드를 `tool(self.<메서드>, parse_docstring=True)`로 감싸 목록으로 돌려준다 (`from langchain.tools import tool`). 메서드 이름이 도구 이름이 되고, `self`는 LLM에게 가지 않는다.
- `build()`에 적은 메서드만 도구가 된다. 공개 메서드는 도구와 `build()`만 두고, 문장 만들기 같은 도우미는 `_`로 시작하는 비공개 메서드로 둔다.
- `parse_docstring=True`면 독스트링의 `Args:`가 LLM이 받는 인자 설명 칸으로 들어가고, 설명의 들여쓰기가 걷힌다. 빼면 메서드 독스트링의 들여쓰기와 `Args:`가 설명 글자에 그대로 붙는다.
- `parse_docstring=True`는 `Args:`가 인자 이름과 맞지 않거나 빠지면 도구를 만들 때 `ValueError`를 낸다. 설명이 코드와 어긋난 채로 서버가 뜨지 않는다.
- **독스트링은 LLM이 읽는 설명서다.** 언제 쓰는지, 언제 쓰면 안 되는지, 인자 형식을 한국어로 쓴다 (`python-style`). `Returns:`는 LLM에게 가지 않으므로 돌려주는 내용은 본문에 적는다.
- 인자에 타입을 적는다. 인자가 많거나 복잡하면 pydantic 모델을 `args_schema`로 쓴다.
- 도구 클래스는 유스케이스만 생성자로 받는다. 포트(저장소 등)를 직접 받지 않고, 서비스 구현과 엔티티를 import하지 않는다.
- 도구 메서드의 인자(주문 번호 등)를 Command/Query로 옮겨 담아 유스케이스에 넘긴다.
- 도구 안에 판단·계산이나 "꺼내기 → 저장" 같은 순서를 적지 않는다. 그것은 도메인과 서비스의 일이다.
- **업무 결과로서의 실패(없음, 권한 없음, 규칙에 걸림)는 예외를 터뜨리지 않고 LLM이 알아들을 문장으로 돌려준다.** 유스케이스가 던진 업무 예외를 도구가 잡아 문장으로 바꾼다. LLM이 그 문장을 보고 사용자에게 안내하거나 다른 도구를 고른다.
- 문장에는 무엇이 문제이고 어떻게 하면 되는지를 적는다. 오류 코드나 스택을 그대로 주지 않는다.
- **외부 시스템 고장(포트 구현이 던진 `UpstreamError`)은 잡지 않는다.** 그대로 올라가 `/chat`이 `UPSTREAM_ERROR`로 끝낸다 (Fail Fast). 고장을 문장으로 바꾸면 LLM이 그 문장을 보고 답을 지어낼 수 있다.
- 예상하지 못한 오류(코드 버그)도 잡지 않는다. 그대로 터져서 드러나야 한다.

```python
class OrderTools:
    """주문 유스케이스를 부르는 도구 묶음. 공개 메서드 하나가 도구 하나다."""

    def __init__(self, orders: OrderUseCase) -> None:
        self._orders = orders

    def build(self) -> list[BaseTool]:
        """에이전트에 넘길 도구 목록을 만든다. 메서드 독스트링이 도구 설명이 된다."""
        return [tool(self.cancel_order, parse_docstring=True)]

    async def cancel_order(self, order_id: str) -> str:
        """주문 번호의 주문을 취소한다. 취소할 수 있는지는 이 도구가 판단한다.

        사용자가 특정 주문을 취소해 달라고 분명히 요청했을 때만 쓴다.
        주문 번호를 모르면 쓰지 말고 사용자에게 주문 번호를 먼저 묻는다.
        결과 문장을 돌려준다. 취소하지 못했으면 그 이유를 담는다.

        Args:
            order_id: 주문 번호. "ORD-"와 숫자 4자리 (예: ORD-1001).
        """
        try:
            await self._orders.cancel_order(CancelOrderCommand(order_id=order_id))
        except OrderNotFoundError:
            return f"주문 {order_id}을(를) 찾을 수 없습니다. 주문 번호를 다시 확인해 주세요."
        except OrderNotCancellableError as e:
            return CANCEL_DENIAL_SENTENCES[e.reason].format(order_id=order_id)
        return f"주문 {order_id}을(를) 취소했습니다."
```

## 구조화 출력

- LLM 답을 정해진 모양으로 받아야 하면 pydantic 모델을 쓴다. 문자열을 직접 잘라 쓰지 않는다.
- `create_agent`: `response_format=<모델>` → 결과의 `structured_response`.
- 단일 호출: `llm.with_structured_output(<모델>)`.
- 모델 필드에 `Field(description=...)`을 한국어로 적는다. LLM이 읽는다.
- 도구 호출을 지원하지 않는 LLM이면 `with_structured_output(<모델>, method="json_mode")`를 시도하고, 그것도 안 되면 프롬프트로 JSON을 요청한 뒤 `<모델>.model_validate_json(...)`으로 검증한다. 검증 실패는 실패 경로로 처리한다.

## 가드레일 연결

```python
# app/application/agent/dto/command.py
@dataclass(frozen=True)
class ChatCommand:
    """에이전트에 넘기는 질문 한 건."""

    conversation_id: str
    message: str


# app/application/agent/service.py — ChatService의 메서드 (한 번에 응답할 때. 스트리밍은 fastapi-conventions)
async def answer(self, command: ChatCommand) -> str:
    """입력 검사 → 답 만들기 → 출력 검사 순서로 답을 만든다."""
    checked = await self._guardrail.check_input(command.message)
    if checked.blocked:
        raise InputBlockedError(checked.message)    # 엔드포인트가 잡아 안내 문구로 답한다
    reply = "".join([text async for text in self._answers.stream(checked.text)])
    return await self._check_output(reply)    # 막히면 OutputBlockedError (agent-architecture의 "채팅 기능")
```

- 출력 검사 결과의 `.text`만 꺼내 쓰지 않는다. 막혔을 때(`blocked`) 가린 글자가 정상 답으로 나간다. 스트리밍과 같은 `_check_output`으로 막힘을 예외로 바꾼다.

- 에이전트 흐름은 요청 모델(`ChatRequest`)이 아니라 Command를 받는다. `ChatRequest`는 `app/presentation`에 있어 `application`이 import할 수 없다 (`agent-architecture`의 "Command").

- 입력 검사는 에이전트 실행 전 한 번, 출력 검사는 최종 답에 한 번 한다.
- 도구 호출 사이마다 검사가 필요하면 미들웨어 클래스(`AgentMiddleware`의 `abefore_model`, `aafter_model`)를 쓴다. 설계 문서에 적힌 경우만.
- 스트리밍 응답의 출력 검사는 `fastapi-conventions`를 따른다.

## 대화 기억

- 대화 기억은 연결 창구(`ConversationMemory`, Redis)로 한다. 요청마다 불러서 `messages` 앞에 붙이고, 답한 뒤 저장한다. 대화 기억을 쓰면 `AnswerGenerator.stream`이 지난 대화도 받도록 포트 모양을 넓힌다 (메시지 타입은 우리 값 묶음으로 둔다).
- LangGraph 체크포인터(`checkpointer=`)를 대화 기억 용도로 쓰지 않는다. 체크포인터는 사람 확인(HITL)처럼 실행을 멈췄다 이어야 할 때만 쓴다.
- 오래된 대화는 개수나 토큰 기준으로 잘라서 넘긴다. 기준은 설계 문서에 적는다.

## 스트리밍

- 글자를 흘려 보낼 때는 `agent.astream(..., stream_mode="messages")`를 쓴다. `(메시지, 메타데이터)`가 차례로 나온다. 이것을 다루는 곳은 답 만들기 어댑터뿐이다.
- 나오는 메시지는 LLM에 따라 다르다. 조각으로 보내는 LLM은 `AIMessageChunk`가 여러 번, 한 번에 보내는 LLM은 `AIMessage`가 한 번 온다. **둘 다 글자로 바꾼다.**
- 도구 호출(`tool_call_chunks`·`tool_calls`가 있는 메시지)과 도구 결과(`ToolMessage`)는 내보내지 않는다. 도구 호출 앞에 LLM이 낸 짧은 말은 나갈 수 있다 (조각이 올 때는 뒤에 도구 호출이 붙을지 알 수 없다).
- 필수 테스트: 조각으로 답하는 가짜(`fake_llm(...)`)와 한 번에 답하는 가짜(`fake_llm(..., streaming=False)`) 둘 다에서 같은 답 글자가 나오는지.

## MCP 도구 연결

- `langchain-mcp-adapters`의 `MultiServerMCPClient`로 MCP 도구를 LangChain 도구로 바꿔 붙인다.
- MCP 서버 주소는 MCP 창구가 준다. 코드에 주소를 적지 않는다.
- MCP 도구도 독스트링(설명)을 확인한다. 설명이 부실하면 LLM이 잘못 고른다.

## 사람 확인 (Human-in-the-loop)

- 돈이 움직이거나 되돌릴 수 없는 일을 하는 도구는 실행 전에 사람 확인을 받는다.
- `create_agent`에 `HumanInTheLoopMiddleware(interrupt_on={"<도구 이름>": True})`와 체크포인터를 넣는다. 확인 후 `Command(resume=...)`으로 이어서 실행한다.
- 어떤 도구에 사람 확인이 필요한지는 설계 문서 도구 표에 적는다.

## 쓰지 않는 예전 방식

| 쓰지 않음 | 대신 |
|---|---|
| `langgraph.prebuilt.create_react_agent` | `langchain.agents.create_agent` |
| `AgentExecutor`, `initialize_agent` | `create_agent` |
| `LLMChain`, `ConversationChain`, `SequentialChain` | 모델·프롬프트를 직접 `ainvoke`, 또는 `StateGraph` |
| `ConversationBufferMemory` 등 `langchain.memory` | 대화 기억 창구 |
| `.run()`, `.predict()`, 체인 직접 호출 `chain(...)` | `.invoke()` / `.ainvoke()` |
| `langchain.chat_models.ChatOpenAI`, `langchain.llms` | `langchain_openai.ChatOpenAI` (LLM 창구 안에서만) |
| `langchain.schema` | `langchain_core.messages`, `langchain_core.documents` |
| `bind_functions`, `functions=` | `bind_tools`, `tools=` |
| `MessageGraph` | `StateGraph` + `messages` 상태 |
| `config_schema=` | `context_schema=` |
| `langchain-classic` 패키지 | 쓰지 않는다 |

새 API가 확실하지 않으면 추측하지 않는다. 설치된 패키지 소스(`.venv/lib/python3.11/site-packages/langchain/`)를 직접 확인한다.
