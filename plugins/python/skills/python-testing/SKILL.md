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
| ① 단위 | 도메인 규칙, 업무 서비스, 도구 함수, 응답 처리, 프롬프트 조립 | 안 씀 | 매번 (`pytest`) |
| ② 가짜 LLM 흐름 | "LLM이 이렇게 답하면 이 도구를 부르고 이렇게 답하는가", 엔드포인트 | 가짜 | 매번 (`pytest`) |
| ③ 연결 확인 | 실제 LLM·Redis·PostgreSQL에 붙는지 | 진짜 | `/python:eval` 시작할 때 |
| ④ 평가 | 답이 쓸 만한지 | 진짜 | `/python:eval`로만 |

- `tests/`에는 ①②만 둔다. 진짜 LLM이나 네트워크를 쓰는 테스트를 `tests/`에 넣지 않는다.
- ③은 테스트 파일을 따로 만들지 않는다. `/python:eval`이 시작할 때 확인하고, 안 되면 평가를 시작하지 않는다.
- ④의 채점 방식은 에이전트를 만든 뒤 실제 답을 보고 사용자와 함께 정한다.

## 가짜(Mock) 규칙

- **바깥에 닿는 것만 가짜로 만든다:** LLM, 연결 창구(`app/application/<기능>/port.py`, `app/application/agent/port.py`, `app/infrastructure/llm/port.py`·`prompt/port.py`의 Protocol), 외부 API, DB, Redis.
- 내 코드 안의 객체(도메인 객체, 상태, 데이터 모델)는 가짜로 만들지 않는다.
- 연결 창구 가짜는 Protocol 모양을 따르는 작은 클래스나 `AsyncMock(spec=<Protocol>)`으로 만든다.
- 테스트는 `.env`를 읽지 않는다. 흐름·엔드포인트 테스트는 `build_platform()`을 부르지 않고 `fake_platform(...)`으로 만든 가짜 묶음을 진짜 조립 함수에 넣는다. `build_platform()` 자체를 확인하는 테스트는 설정(`fake_settings()`)을 직접 넘겨 부른다. `lifespan`은 아래 "서버 시작(lifespan) 테스트"를 따른다.

### 가짜 LLM

`GenericFakeChatModel`은 정해 둔 메시지를 차례로 돌려준다. 도구 호출 답은 `AIMessage(tool_calls=[...])`로 만든다.

뼈대의 `tests/fakes.py`에 있는 가짜를 쓴다. 새로 만들지 않는다.

| 가짜 | 하는 일 |
|---|---|
| `fake_llm(*replies)` | 답을 차례로 돌려주는 가짜 LLM을 만든다. 답 자리에 예외를 넣으면 그 차례의 LLM 호출이 실패한다. `streaming=False`면 조각 없이 한 번에 답하는 LLM처럼 군다 |
| `FakeToolCallingModel.received` | 호출마다 받은 메시지 목록. LLM을 불렀는지, 검사를 거친 문장을 받았는지 확인한다 |
| `FakeGuardrail` | 정해 둔 문장만 막거나 바꾸고 나머지는 통과시킨다. 검사에 들어온 문장을 기록한다. `input_delay`·`output_delay`로 검사마다 기다리게 할 수 있다 (시간 초과 테스트용) |
| `fake_platform(llm, ...)` | 가짜 창구로 구현 묶음(`Platform`)을 만든다. 이것을 진짜 조립 함수(`app/container.py`)에 넣는다 |
| `fake_settings(platform="")` | `.env` 대신 쓰는 설정. LLM 칸에 가짜 주소·키가 들어 있다. `build_platform()`·`lifespan` 테스트에 넘긴다 |

- `GenericFakeChatModel`은 `bind_tools`가 없고 스트리밍에서 도구 호출을 조각으로 내지 못한다. `FakeToolCallingModel`이 이 둘을 메운다. `GenericFakeChatModel`을 그대로 쓰면 `create_agent`와 `astream(stream_mode="messages")`에서 오류가 난다.
- 이 가짜는 langchain-core 내부 동작에 기댄다. `tests/test_fakes.py`가 그 동작을 확인하므로 지우지 않는다.
- 창구가 늘면(저장소 등) `fake_platform`에 인자를 더하고 그 창구의 가짜를 `tests/fakes.py`에 둔다. 테스트 파일 안에서 같은 가짜를 따로 만들지 않는다.
- 저장소 가짜는 아래 모양으로 만든다. `AsyncMock(spec=...)`의 메서드는 아무것도 정하지 않으면 `None`이 아니라 가짜 객체를 돌려주므로, 찾기 메서드에 "없으면 `None`"을 정해 둔다.

```python
def fake_order_repository(*orders: Order) -> AsyncMock:
    """orders를 주문 번호로 찾아 주는 가짜 저장소. 없는 번호는 None."""
    by_id = {order.order_id: order for order in orders}
    repository = AsyncMock(spec=OrderRepository)
    repository.find.side_effect = by_id.get
    return repository
```

- 저장한 것은 `repository.save.assert_awaited_once_with(...)`로 확인한다.

```python
llm = fake_llm(
    AIMessage(content="", tool_calls=[
        {"name": "get_product", "args": {"product_id": "P001"}, "id": "call-1"},
    ]),
    AIMessage(content="P001 아메리카노는 4,500원입니다."),
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
| 행위검증 | 무엇을 어떻게 불렀나 | `repository.find.assert_awaited_once_with("P001")` |

- ① 단위 테스트는 상태검증이 중심이다. ② 흐름 테스트는 행위검증(어떤 도구를, 어떤 인자로, 가드레일을 거쳤나)이 중심이다.

```python
@pytest.mark.anyio
async def test_상품을_물으면_상품_조회_도구를_부른다() -> None:
    # Given
    repository = fake_product_repository(Product(product_id="P001", name="아메리카노", price=4500))
    platform = fake_platform(fake_llm(...), products=repository)
    chat = build_chat_service(platform, timeout_seconds=30)

    # When
    command = ChatCommand(conversation_id="c-1", message="P001 얼마예요?")
    answer = "".join([s async for s in chat.stream_answer(command)])

    # Then
    repository.find.assert_awaited_once_with("P001")
    assert "4,500원" in answer
```

- 가짜는 포트 자리에만 넣는다. 서비스·도구·에이전트는 진짜 조립 함수(`app/container.py`)가 만든 것을 쓴다. 테스트용 조립 코드를 따로 만들지 않는다.

### 서비스와 도구의 단위 테스트

| 대상 | 만드는 법 | 확인하는 것 |
|---|---|---|
| 서비스 | 진짜 서비스 + 가짜 나가는 포트 (`AsyncMock(spec=<Protocol>)`) | 순서, 던지는 예외, 규칙에 걸리면 저장하지 않는 것, 엔티티가 아니라 Result를 돌려주는 것 |
| 도구 | 진짜 서비스(가짜 포트를 넣은 것)를 유스케이스 자리에 넣어 도구를 만든다 | Result와 예외가 어떤 문장으로 바뀌는지 |

- 도구를 테스트할 때 서비스를 가짜로 만들지 않는다. 서비스는 내 코드다. 진짜 서비스를 지나야 서비스가 실제로 던지는 예외를 도구가 잡는지 확인된다.
- 도구 테스트에서 순서나 저장 여부를 다시 확인하지 않는다. 그것은 서비스 테스트의 몫이다.
- 도구의 표시용 표(상태 이름, 사유별 문장)가 Enum의 모든 값을 담고 있는지 테스트로 확인한다. 도메인에 값을 더하고 표를 빠뜨리면 여기서 드러난다.

### 실패 경로 — 필수

| 실패 | 확인할 것 |
|---|---|
| 도구 오류 (결과 없음, 업무 규칙에 걸림) | 예외가 터지지 않고 안내 문장이 LLM에게 간다 |
| 외부 시스템 고장 (포트 구현이 던진 `UpstreamError`) | 도구가 문장으로 바꾸지 않는다. 조립한 흐름에서도 삼켜지지 않고 올라와 LLM을 다시 부르지 않는다 |
| 업무 서비스 실패 | 서비스가 예외를 던지고(문장을 만들지 않는다), 규칙에 걸리면 저장하지 않는다 |
| LLM 출력 형식 깨짐 (구조화 출력 실패) | 정해 둔 실패 처리로 간다 |
| 빈 검색 결과 | 지어내지 않고 없다는 안내를 한다 (가짜 LLM 흐름으로 확인) |
| 가드레일 | 입력 검사가 LLM보다 먼저, 출력 검사가 답보다 먼저 불린다. 막히면 LLM을 부르지 않는다 |
| 시간 초과 | `TIMEOUT` 안내를 돌려준다 |

## 엔드포인트 테스트

- `TestClient(app)`로 서버를 띄우지 않고 부른다. `app.state.chat`에 가짜 창구로 조립한 채팅 서비스(`build_chat_service(fake_platform(...), ...)`)를 `monkeypatch.setattr(app.state, "chat", ..., raising=False)`로 넣는다. `app`은 모듈 하나를 같이 쓰므로 직접 대입하면 다음 테스트로 값이 샌다.
- **엔드포인트 테스트에서는 `with TestClient(app)`를 쓰지 않는다.** `with`로 열면 `lifespan`이 돌아 `.env`를 읽고, 넣어 둔 가짜 `app.state.chat`을 진짜로 덮어쓴다.
- 엔드포인트마다 정상 1개 이상, 요청 형식 오류(422) 1개.
- SSE는 본문을 빈 줄로 나눠 이벤트 목록으로 만든 뒤 `token`들 → `done` 순서와 `data` JSON을 확인한다. 실패 경로는 `error` 이벤트로 끝나는지 확인한다.

### 서버 시작(lifespan) 테스트

`lifespan`을 확인하는 테스트만 `with TestClient(app)`를 쓴다. `.env`를 읽지 않도록 `main.load_settings`를 가짜 설정으로 바꾼다. 뼈대의 `tests/test_main.py`가 이 방식으로 서버가 켜지고 꺼지는지만 확인한다. 채팅 기능을 만들면 아래처럼 `app.state.chat`을 확인하는 테스트를 더한다.

```python
def test_서버가_켜지면_채팅_서비스를_조립해_둔다(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: .env 대신 가짜 설정. 로컬 창구를 만들지만 LLM은 부르지 않는다.
    monkeypatch.setattr("main.load_settings", fake_settings)
    monkeypatch.setattr(app.state, "chat", None, raising=False)    # 끝나면 되돌린다

    # When
    with TestClient(app):
        chat = app.state.chat

    # Then
    assert isinstance(chat, ChatService)
```

## 기준 — 커버리지 + 필수 테스트

둘 다 만족해야 python-reviewer가 통과시킨다.

| 기준 | 내용 |
|---|---|
| 커버리지 | `app/` 기준 80% 이상 |
| 필수 테스트 | 업무 서비스 메서드와 도구 함수마다 성공 1개 + 실패 1개 |
| | 에이전트 흐름마다 대표 경로 1개 (설계 문서 시퀀스 다이어그램의 대표 질문) |
| | 엔드포인트마다 정상 1개 이상 + 요청 형식 오류(422) 1개 |
| | 위 "실패 경로 — 필수" 표 |

- **뼈대 코드의 필수 테스트는 뼈대 테스트가 맡는다.** 답 만들기 어댑터(조각·한 번에 답하는 LLM, LLM 실패, 도구 버그), `within_time_limit`(전체 시간 기준), `stream_sentences`, `sse_response`(막힘·오류 이벤트)는 뼈대의 `tests/`에 테스트가 있다. 그 코드를 고치지 않았으면 기능마다 다시 쓰지 않는다. 고쳤으면 그 테스트를 함께 고친다.
- 기능 테스트는 기능 코드가 그 길을 실제로 지나는지만 확인한다 (예: `/chat`이 시간 초과·LLM 실패에서 `error` 이벤트로 끝나는지, 저장소 고장이 흐름에서 삼켜지지 않는지).

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
