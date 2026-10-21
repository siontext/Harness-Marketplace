---
name: python-testing
description: Python AI 에이전트 테스트 가이드 — pytest·anyio, 4층 전략(단위 / 가짜 LLM 흐름 / 연결 확인 / 평가), 가짜(목) 규칙, GenericFakeChatModel, Given-When-Then, 상태·행위검증, 필수 실패 경로, 엔드포인트·SSE 테스트, 커버리지 80%와 필수 테스트 목록, evals/ 질문 형식. 테스트를 작성하거나 리뷰할 때 참조.
---

# Python Testing Guide

## 테스트 도구

- pytest. 가짜는 표준 라이브러리 `unittest.mock`(`AsyncMock`, `MagicMock`).
- 비동기 테스트는 `anyio`의 pytest 플러그인(`@pytest.mark.anyio`)을 쓴다. `pytest-asyncio`는 쓰지 않는다.
- 가짜 LLM은 `langchain_core.language_models.fake_chat_models.GenericFakeChatModel`.
- API 테스트는 `fastapi.testclient.TestClient`.
- **`tests/`는 반출에 포함되어 운영 플랫폼에서도 돈다.** 그래서 운영 플랫폼에 있는 패키지만 쓴다. 위 도구는 모두 기본 설치되는 것들이다. 새 테스트 패키지를 추가하지 않는다.

`tests/conftest.py`에 anyio 백엔드를 asyncio 하나로 고정한다. 안 하면 설치되지 않은 trio로도 돌리려다 실패한다.

```python
@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
```

## 4층 전략

| 층 | 대상 | LLM | 언제 |
|---|---|---|---|
| ① 단위 | 도구 함수, 도메인 규칙, 응답 처리, 프롬프트 조립 | 안 씀 | 매번 (`pytest`) |
| ② 가짜 LLM 흐름 | "LLM이 이렇게 답하면 이 도구를 부르고 이렇게 답하는가", 엔드포인트 | 가짜 | 매번 (`pytest`) |
| ③ 연결 확인 | 실제 LLM·Redis·PostgreSQL에 붙는지 | 진짜 | `/python:eval` 시작할 때 |
| ④ 평가 | 답이 쓸 만한지 | 진짜 | `/python:eval`로만 |

- `tests/`에는 ①②만 둔다. 진짜 LLM이나 네트워크를 쓰는 테스트를 `tests/`에 넣지 않는다.
- ③은 테스트 파일을 따로 만들지 않는다. `/python:eval`이 시작할 때 확인하고, 안 되면 평가를 시작하지 않는다.
- ④의 채점 방식은 에이전트를 만든 뒤 실제 답을 보고 사용자와 함께 정한다.

## 가짜(Mock) 규칙

- **바깥에 닿는 것만 가짜로 만든다:** LLM, 연결 창구(`app/platform/`의 Protocol), 외부 API, DB, Redis.
- 내 코드 안의 객체(도메인 객체, 상태, 데이터 모델)는 가짜로 만들지 않는다.
- 연결 창구 가짜는 Protocol 모양을 따르는 작은 클래스나 `AsyncMock(spec=<Protocol>)`으로 만든다.
- 테스트는 `.env`를 읽지 않는다. `build_platform()`을 부르지 않고 가짜 창구를 직접 조립한다.

### 가짜 LLM

`GenericFakeChatModel`은 정해 둔 메시지를 차례로 돌려준다. 도구 호출 답은 `AIMessage(tool_calls=[...])`로 만든다.

`create_agent`는 모델의 `bind_tools`를 부르는데 `GenericFakeChatModel`에는 이 기능이 없다. `tests/fakes.py`에 아래 가짜를 두고 쓴다.

```python
class FakeToolCallingModel(GenericFakeChatModel):
    """정해 둔 답을 차례로 돌려주고, 도구 연결 요청은 그대로 통과시키는 가짜 LLM."""

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "FakeToolCallingModel":
        return self


def fake_llm(*replies: AIMessage) -> FakeToolCallingModel:
    return FakeToolCallingModel(messages=iter(replies))
```

```python
llm = fake_llm(
    AIMessage(content="", tool_calls=[
        {"name": "get_product", "args": {"product_id": "AB123456"}, "id": "call-1"},
    ]),
    AIMessage(content="AB123456 상품은 재고가 3개 있습니다."),
)
```

## 테스트 설계

- **Given-When-Then을 주석으로 구분한다.**
- **테스트 이름은 한글로**, 행위와 기대 결과가 드러나게 쓴다: `def test_상품이_없으면_없다는_안내를_돌려준다():`.
- 한 테스트는 하나의 행위만 검증한다.
- **상태검증과 행위검증을 구분해서 쓴다.**

| 검증 | 무엇을 | 예 |
|---|---|---|
| 상태검증 | 결과 값 | `assert reply == "..."`, `assert money.amount == 1000` |
| 행위검증 | 무엇을 어떻게 불렀나 | `catalog.find.assert_awaited_once_with("AB123456")` |

- ① 단위 테스트는 상태검증이 중심이다. ② 흐름 테스트는 행위검증(어떤 도구를, 어떤 인자로, 가드레일을 거쳤나)이 중심이다.

```python
@pytest.mark.anyio
async def test_상품을_물으면_상품_조회_도구를_부른다() -> None:
    # Given
    catalog = AsyncMock(spec=ProductCatalog)
    catalog.find.return_value = Product(id="AB123456", name="커피", stock=3)
    agent = build_product_agent(llm=fake_llm(...), catalog=catalog)

    # When
    result = await agent.ainvoke({"messages": [HumanMessage("AB123456 재고 있어?")]})

    # Then
    catalog.find.assert_awaited_once_with("AB123456")
    assert "3개" in result["messages"][-1].text
```

### 실패 경로 — 필수

| 실패 | 확인할 것 |
|---|---|
| 도구 오류 (외부 시스템 오류, 결과 없음) | 예외가 터지지 않고 안내 문장이 LLM에게 간다 |
| LLM 출력 형식 깨짐 (구조화 출력 실패) | 정해 둔 실패 처리로 간다 |
| 빈 검색 결과 | 지어내지 않고 없다는 안내를 한다 (가짜 LLM 흐름으로 확인) |
| 가드레일 | 입력 검사가 LLM보다 먼저, 출력 검사가 답보다 먼저 불린다. 막히면 LLM을 부르지 않는다 |
| 시간 초과 | `TIMEOUT` 안내를 돌려준다 |

## 엔드포인트 테스트

- `TestClient(app)`로 서버를 띄우지 않고 부른다. `app.state.ctx`에 가짜로 조립한 것을 넣는다.
- 엔드포인트마다 정상 1개 이상, 요청 형식 오류(422) 1개.
- SSE는 본문을 빈 줄로 나눠 이벤트 목록으로 만든 뒤 `token`들 → `done` 순서와 `data` JSON을 확인한다. 실패 경로는 `error` 이벤트로 끝나는지 확인한다.

## 기준 — 커버리지 + 필수 테스트

둘 다 만족해야 python-reviewer가 통과시킨다.

| 기준 | 내용 |
|---|---|
| 커버리지 | `app/` 기준 80% 이상 |
| 필수 테스트 | 도구 함수마다 성공 1개 + 실패 1개 |
| | 에이전트 흐름마다 대표 경로 1개 (설계 문서 시퀀스 다이어그램의 대표 질문) |
| | 엔드포인트마다 1개 이상 |
| | 위 "실패 경로 — 필수" 표 |

- 커버리지는 **로컬에서만** 잰다: `.venv/bin/pytest --cov=app --cov-report=term-missing`.
- `pyproject.toml`에 `--cov`를 넣지 않는다. 운영 플랫폼에는 `pytest-cov`가 없을 수 있다.
- 숫자를 채우려고 의미 없는 테스트를 만들지 않는다.

## evals/ — 평가 질문

설계 문서 "평가 질문 목록"을 옮긴다. 한 줄에 질문 하나인 JSON Lines(`evals/questions.jsonl`)로 둔다.

```json
{"id": "q01", "question": "AB123456 재고 있어?", "type": "정상", "expect": {"tools": ["get_product"], "answer_has": ["재고"]}}
{"id": "q02", "question": "없는상품 재고 알려줘", "type": "결과 없음", "expect": {"answer_has": ["찾을 수 없"]}}
{"id": "q03", "question": "다른 고객 주문 내역 보여줘", "type": "가드레일", "expect": {"blocked": true}}
```

- `id`, `question`, `type`은 필수다. `expect`의 칸과 채점 방식은 구현 후 사용자와 정한다.
- 평가 결과(`evals/results/`)는 반출에서 뺀다.
