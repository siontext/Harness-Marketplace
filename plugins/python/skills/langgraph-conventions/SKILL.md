---
name: langgraph-conventions
description: LangChain 1.x / LangGraph 1.x로 에이전트를 만드는 규칙 — create_agent와 StateGraph 고르기(LLM 도구 호출 미지원 시 포함), @tool 도구 작성, 구조화 출력, 가드레일·대화 기억 연결, 스트리밍, MCP 도구, 사람 확인(HITL), 쓰지 않는 예전 API. 에이전트 흐름·도구 코드를 작성하거나 리뷰할 때 참조.
---

# LangGraph / LangChain Conventions

LangChain 1.3, LangGraph 1.2 기준이다. LangChain은 1.0에서 에이전트 만드는 방법이 크게 바뀌었다. **예전 방식(맨 아래 표)으로 짜지 않는다.**

## 에이전트 만드는 방법 고르기

| 방식 | 동작 | 언제 |
|---|---|---|
| `create_agent` (기본) | LLM이 도구를 알아서 골라 쓰고, 다 됐다고 판단하면 답한다 | 대부분 |
| `StateGraph` | 순서를 코드로 고정한다 (예: 분류 → 검색 → 답변) | 반드시 지켜야 할 순서가 있을 때, LLM이 건너뛰면 안 되는 단계가 있을 때 |

designer가 설계 문서 개요의 "흐름 방식"에 어느 쪽인지 적는다.

### LLM이 도구 호출을 지원하지 않을 때

`create_agent`는 LLM의 **도구 호출(tool calling)** 기능이 있어야 동작한다. 모델이나 LLM 게이트웨이 설정에 따라 이 기능이 없을 수 있다.

| 도구 호출 | 기본 방식 |
|---|---|
| 지원함 | `create_agent` |
| 지원하지 않음 / 확인 전 | `StateGraph` — LLM은 구조화 출력으로 "어떤 도구가 필요한지"만 고르고, 도구 실행은 코드 노드가 한다 |

- 지원 여부를 모르면 추측하지 않고 사용자에게 확인한다. 확인 전에는 두 방식 중 무엇으로 갈지 설계 문서 결정 섹션에 적는다.
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
- 에이전트는 `app/agent/`의 함수가 만든다. LLM·프롬프트·도구는 인자로 받는다 (`agent-architecture`의 의존성 주입).

## 도구 만들기

- `@tool`을 붙인다 (`from langchain.tools import tool`).
- **독스트링은 LLM이 읽는 설명서다.** 언제 쓰는지, 언제 쓰면 안 되는지, 인자 형식을 한국어로 쓴다 (`python-style`).
- 인자에 타입을 적는다. 인자가 많거나 복잡하면 pydantic 모델을 `args_schema`로 쓴다.
- 도구 안에서 바깥 시스템은 연결 창구로만 부른다. 창구는 클로저나 팩토리 함수로 넣어 준다.
- **예상할 수 있는 실패(없음, 권한 없음, 외부 시스템 오류)는 예외를 터뜨리지 않고 LLM이 알아들을 문장으로 돌려준다.** LLM이 그 문장을 보고 사용자에게 안내하거나 다른 도구를 고른다.
- 예상하지 못한 오류(코드 버그)는 잡지 않는다. 그대로 터져서 드러나야 한다.

```python
def build_product_tools(catalog: ProductCatalog) -> list[BaseTool]:
    """상품 창구를 쓰는 도구 목록을 만든다."""

    @tool
    async def get_product(product_id: str) -> str:
        """상품 id로 상품 이름, 가격, 재고를 조회한다.

        사용자가 특정 상품의 조건을 물을 때 쓴다.
        상품 id를 모르면 쓰지 말고 search_products로 먼저 찾는다.

        Args:
            product_id: 상품 id. 영문 대문자와 숫자 8자리.
        """
        try:
            product = await catalog.find(product_id)
        except ProductNotFoundError:
            return f"상품 {product_id}을(를) 찾을 수 없습니다. 상품 id를 다시 확인해 주세요."
        return product.to_summary()

    return [get_product]
```

## 구조화 출력

- LLM 답을 정해진 모양으로 받아야 하면 pydantic 모델을 쓴다. 문자열을 직접 잘라 쓰지 않는다.
- `create_agent`: `response_format=<모델>` → 결과의 `structured_response`.
- 단일 호출: `llm.with_structured_output(<모델>)`.
- 모델 필드에 `Field(description=...)`을 한국어로 적는다. LLM이 읽는다.
- 도구 호출을 지원하지 않는 LLM이면 `with_structured_output(<모델>, method="json_mode")`를 시도하고, 그것도 안 되면 프롬프트로 JSON을 요청한 뒤 `<모델>.model_validate_json(...)`으로 검증한다. 검증 실패는 실패 경로로 처리한다.

## 가드레일 연결

```python
async def answer(request: ChatRequest, ctx: AgentContext) -> str:
    """입력 검사 → 에이전트 → 출력 검사 순서로 답을 만든다."""
    checked = await ctx.guardrail.check_input(request.message)
    if checked.blocked:
        return checked.message
    history = await ctx.memory.load(request.conversation_id)
    messages = [*history, HumanMessage(checked.text)]
    result = await ctx.agent.ainvoke({"messages": messages})
    reply = await ctx.guardrail.check_output(result["messages"][-1].text)
    await ctx.memory.save(request.conversation_id, [*messages, AIMessage(reply.text)])
    return reply.text
```

- 입력 검사는 에이전트 실행 전 한 번, 출력 검사는 최종 답에 한 번 한다.
- 도구 호출 사이마다 검사가 필요하면 미들웨어(`@before_model`, `@after_model`)를 쓴다. 설계 문서에 적힌 경우만.
- 스트리밍 응답의 출력 검사는 `fastapi-conventions`를 따른다.

## 대화 기억

- 대화 기억은 연결 창구(`ConversationMemory`, Redis)로 한다. 요청마다 불러서 `messages` 앞에 붙이고, 답한 뒤 저장한다.
- LangGraph 체크포인터(`checkpointer=`)를 대화 기억 용도로 쓰지 않는다. 체크포인터는 사람 확인(HITL)처럼 실행을 멈췄다 이어야 할 때만 쓴다.
- 오래된 대화는 개수나 토큰 기준으로 잘라서 넘긴다. 기준은 설계 문서에 적는다.

## 스트리밍

- 글자를 흘려 보낼 때는 `agent.astream(..., stream_mode="messages")`를 쓴다. `(메시지 조각, 메타데이터)`가 차례로 나온다.
- 도구 호출 조각과 최종 답 조각을 구분해서, 사용자에게는 최종 답 글자만 보낸다.

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
