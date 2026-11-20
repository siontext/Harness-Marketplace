---
name: fastapi-conventions
description: 에이전트를 앱·다른 서버가 부를 수 있게 여는 FastAPI 창구 규칙 — main.py(lifespan)와 app/presentation 파일 배치(routes·schemas·errors·response), /chat·/health, pydantic 요청·응답, 공통 응답 틀(ApiResponse·SseEvent), SSE 스트리밍(기본)과 한 번에 응답(대안), 스트리밍 중 출력 가드레일, 오류 응답 통일, 시간 제한. main.py나 app/presentation 코드를 작성하거나 리뷰할 때 참조.
---

# FastAPI Conventions

에이전트는 혼자서는 바깥과 이야기하지 못한다. 호출하는 쪽(앱, 다른 서버)이 `/chat`으로 질문을 보내면 FastAPI가 받아 에이전트에 넘기고 답을 돌려준다. FastAPI를 아는 코드는 `main.py`와 `app/presentation/`에만 둔다.

## 파일 배치

| 파일 | 두는 것 |
|---|---|
| `main.py` | `FastAPI` 앱 만들기, `lifespan`, 엔드포인트·예외 핸들러 붙이기. 엔드포인트나 모델을 직접 적지 않는다 |
| `app/presentation/routes.py` | 엔드포인트 (`APIRouter`) |
| `app/presentation/schemas.py` | 엔드포인트별 요청·응답 내용 (`ChatRequest`, `HealthStatus` 등). 공통 응답 틀은 두지 않는다 |
| `app/presentation/errors.py` | 오류 규칙 값, 예외 → 규칙 대응표, 전역 예외 핸들러 (`register_exception_handlers`) |
| `app/presentation/response/api_response.py` | `ApiResponse` — JSON 응답의 공통 틀 |
| `app/presentation/response/sse_event.py` | `SseEvent` — 스트리밍 이벤트의 공통 틀 |
| `app/presentation/response/error_code.py` | `ErrorCode` — 오류 응답의 `code` 값 |
| `app/presentation/response/messages.py` | 사용자에게 보여줄 안내 문구 |

- `app/presentation`은 `app/application`을 부르고, 그 반대는 금지다. `app/infrastructure`는 import하지 않는다 (`agent-architecture`).
- 응답 틀은 종류마다 `app/presentation/response/`에 파일 하나로 둔다. 목록 조회가 생기면 `page_response.py`(`PageResponse`)를 더한다.
- 그 밖에 `app/presentation/` 안에 파일을 더 만들 때는 설계 문서에 적힌 경우만.

## main.py — 시작·종료 조립

- 서버가 켜질 때 `lifespan`에서 연결 창구(`build_platform()`)를 만들고 `app/container.py`의 조립 함수로 에이전트를 **한 번** 만든다. 요청마다 만들지 않는다.
- 만든 것은 `app.state`에 둔다. 엔드포인트는 `request.app.state`에서 꺼내 쓴다.
- 서버가 꺼질 때 연결(Redis, DB, HTTP 클라이언트)을 닫는다.
- 연결 창구를 불러오지 못하면 서버가 뜨지 않게 그대로 오류를 낸다 (`agent-architecture`).

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = load_settings()
    platform = build_platform(settings)
    app.state.ctx = build_agent_context(platform, settings.agent_timeout_seconds)
    yield
    await platform.aclose()


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
app.include_router(router)
```

- `@app.on_event("startup")`은 쓰지 않는다 (예전 방식).
- 엔드포인트는 `async def`로 쓴다. 안에서 동기 블로킹 호출 금지 (`python-style`).

## 주소

| Method | Path | 하는 일 |
|---|---|---|
| POST | `/chat` | 질문을 받아 답한다 |
| GET | `/health` | 서버가 살아 있는지 알려 준다. `{"status": "ok"}` |

- `/health`는 LLM이나 DB를 부르지 않는다. 서버 프로세스가 응답하는지만 본다.
- `/health`는 `ApiResponse`로 감싸지 않는다. 운영 플랫폼이 본문을 읽어 판단할 수 있다.
- 주소를 더 만들 때는 설계 문서에 적힌 경우만.

## 요청·응답 모양

pydantic 모델로 정한다. 필드 설명은 한국어 `Field(description=...)`.

```python
class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=1, description="대화 id. 같은 대화는 같은 값")
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH, description="사용자 질문")
```

- 요청 모델에서 길이·형식을 검사한다. 검사 실패는 FastAPI가 422로 돌려준다.
- 엔드포인트는 요청 모델을 Command(`ChatCommand`)로 바꿔 에이전트에 넘긴다. 요청 모델을 `application`에 그대로 넘기지 않는다 (`agent-architecture`의 "Command").
- 호출하는 쪽과 다른 모양이 필요하면 설계 문서 개요에 적고 그에 맞춘다.

## 공통 응답 틀

JSON으로 답하는 엔드포인트는 성공이든 실패든 `ApiResponse` 하나로 감싼다. `/health`만 예외다.

| 칸 | 성공 | 실패 |
|---|---|---|
| `code` | `"SUCCESS"` | 오류 종류 (`ErrorCode`) |
| `message` | `null` | 사용자에게 보여줄 안내 문구 |
| `data` | 돌려줄 내용 | `null` |

```python
@router.post("/orders")
async def create_order(body: OrderRequest) -> ApiResponse[OrderResult]:
    return ApiResponse.success(OrderResult(order_id="o-123"))
```

```json
{"code": "SUCCESS", "message": null, "data": {"order_id": "o-123"}}
```

- 엔드포인트의 반환 타입은 `ApiResponse[내용 모델]`로 적는다. 내용 모델은 `app/presentation/schemas.py`에 둔다.
- 성공은 `ApiResponse.success(...)`, 실패는 `ApiResponse.fail(...)`로 만든다. 실패는 전역 예외 핸들러만 만든다.
- `dict`를 그대로 돌려주지 않는다.
- 스트리밍 응답은 `ApiResponse`로 감싸지 않고 `SseEvent`를 쓴다 (아래 "SSE 이벤트 모양").

## 응답 방식 — 기본은 SSE

| 방식 | 동작 | 언제 |
|---|---|---|
| **SSE 스트리밍 (기본)** | 연결 하나를 열어 두고 글자가 나오는 대로 보낸다 (`text/event-stream`) | 채팅 화면에 글자를 흘려 보여줄 때 |
| 한 번에 응답 | 답을 다 만든 뒤 JSON 하나로 보낸다 | 호출하는 쪽이 SSE를 받지 못할 때 |

한 프로젝트에서 `/chat`은 한 방식만 쓴다. 어느 쪽인지는 설계 문서 개요의 "응답 방식"을 따른다.

### SSE 이벤트 모양

```text
event: token
data: {"text": "주문하시면"}

event: token
data: {"text": " 내일 도착합니다."}

event: done
data: {"conversation_id": "c-123"}
```

| event | data | 뜻 |
|---|---|---|
| `token` | `{"text": "..."}` | 답의 다음 조각 |
| `done` | `{"conversation_id": "..."}` | 답 끝 |
| `error` | `{"code": "...", "message": "..."}` | 실패. 이 뒤로 아무것도 보내지 않는다 |

- 이벤트는 `SseEvent.token(...)`, `SseEvent.done(...)`, `SseEvent.error(...)`로 만들고 `encode()`로 보낼 글자를 얻는다. 이벤트 글자를 직접 이어 붙이지 않는다.
- `StreamingResponse(..., media_type="text/event-stream")`로 보낸다. 헤더에 `Cache-Control: no-cache`를 넣는다.
- `data`는 JSON 한 줄이고 이벤트 하나는 빈 줄(`\n\n`)로 끝난다. 줄바꿈이 들어간 글자를 그대로 쓰면 이벤트가 깨진다. `encode()`가 이 모양을 맞춘다.
- 스트리밍이 시작된 뒤에는 HTTP 상태 코드를 바꿀 수 없다. 실패는 `error` 이벤트로 알린다.
- 대화 기억·기록 저장은 `done`을 보내기 직전에 한다.

### 스트리밍 중 출력 가드레일

이미 보낸 글자는 되돌릴 수 없다. 그래서 **검사하고 나서 보낸다.**

- LLM 조각을 문장 단위로 모아 출력 가드레일을 거친 뒤 `token`으로 보낸다. 가드레일이 돌려준 문장(가려졌을 수 있다)을 보낸다.
- 문장이 끝나는 자리는 아래 기준으로 잡는다. 마지막에 남은 글자는 끝에서 한 번 더 검사해 보낸다.

| 끊는 자리 | 예 |
|---|---|
| 마침표·물음표·느낌표(`. ! ?` 와 `。！？`) 뒤에 공백이 올 때 | `...했습니다. 다음은` |
| 줄이 바뀔 때 | 목록의 각 줄 |
| 끊지 않는다: 점 뒤에 공백이 없을 때 | `3.5일`, `a@b.com` |
| 끊지 않는다: 숫자 바로 뒤의 점 | `1. 첫째` (목록 번호) |

```python
_SENTENCE_END = re.compile(r"(?<![0-9])[.!?。！？]+\s+|\n+")
```

- 문장이 끝나지 않았는데 길다고 중간에서 끊어 보내지 않는다. 가려야 할 값이 둘로 나뉘어 검사를 빠져나갈 수 있다.
- 운영 플랫폼 가드레일이 스트리밍 검사(조각을 이어서 검사하는 세션)를 제공하면 그것을 쓴다.
- 검사에서 막히면 그 자리에서 `error` 이벤트(`code`: `BLOCKED`, `message`: 안내 문구)를 보내고 끝낸다. 막힌 내용은 대화 기록에 "차단됨"으로 남긴다.
- 입력 가드레일은 스트리밍과 상관없이 LLM을 부르기 전에 한 번 한다.

#### 막혔을 때 알리는 방법

| 막힌 곳 | 에이전트 흐름(`application`)이 하는 일 | `/chat`이 보내는 것 |
|---|---|---|
| 입력 | LLM을 부르지 않고 가드레일의 안내 문구를 답으로 내보낸다 (예외 없음) | `token`(안내 문구) → `done` |
| 출력 | `OutputBlockedError`를 던진다. 더 진행할 수 없으므로 무시할 수 없게 한다 | `error` · `BLOCKED` |

```python
try:
    async for sentence in stream_answer(command, ctx):
        yield SseEvent.token(sentence).encode()
except OutputBlockedError as e:        # 의도된 결과: 이름을 적어 따로 잡는다
    logger.warning("출력 가드레일 차단: %s %s", request.method, request.url.path)
    yield SseEvent.error(ErrorCode.BLOCKED, e.guard_message or messages.BLOCKED).encode()
    return
# 스트리밍이 시작된 뒤의 마지막 경계다. 전역 핸들러와 같은 대응표로 답한다.
except Exception as exc:
    rule = find_error_rule(exc)
    log_failure(request, rule, exc, streaming=True)
    yield SseEvent.error(rule.code, rule.message).encode()
    return
yield SseEvent.done(command.conversation_id).encode()
```

- `OutputBlockedError`는 `app/application/agent/`에 두고 가드레일이 준 안내 문구를 담는다. 문구가 비어 있으면 `/chat`이 `messages.BLOCKED`를 쓴다.
- **`OutputBlockedError`를 오류 대응표(`ERROR_RULES`)에 넣지 않는다.** 막힌 것은 오류가 아니라서 상태 코드가 없다. LLM 실패 같은 오류와 같은 `except`에서 처리하지 않는다.
- 로그에는 막혔다는 사실만 남기고 막힌 내용은 남기지 않는다.
- 한 번에 응답 방식에서는 엔드포인트가 `OutputBlockedError`를 잡아 안내 문구를 정상 답(200)으로 돌려준다.

### 한 번에 응답 (대안)

```python
class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
```

호출하는 쪽이 SSE를 받지 못하면 `/chat`이 `ApiResponse[ChatResponse]`를 JSON으로 돌려주게 바꾼다. 이때 `app/application/agent/`에 한 번에 답하는 함수를 더하고 `app/presentation/routes.py`의 엔드포인트를 바꾼다. 에이전트 조립, 도구, 서비스는 그대로다.

- 설계 문서의 응답 방식에 해당하는 함수만 만든다. 쓰지 않는 방식의 함수를 미리 만들어 두지 않는다.

## 오류 응답 통일

| 상황 | 상태 코드 | code |
|---|---|---|
| 요청 형식 오류 | 422 | `INVALID_REQUEST` |
| 입력 가드레일에 막힘 | 200 (안내 문구가 답) | — |
| 출력 가드레일에 막힘 | 200 (안내 문구가 답). 스트리밍 중이면 `error` 이벤트 | `BLOCKED` |
| 시간 초과 | 504 (스트리밍 중이면 `error` 이벤트) | `TIMEOUT` |
| LLM·외부 시스템 오류 | 502 (스트리밍 중이면 `error` 이벤트) | `UPSTREAM_ERROR` |
| 그 밖의 오류 | 500 | `INTERNAL_ERROR` |

- 오류 본문은 항상 `ApiResponse` 실패 모양(`{"code": "...", "message": "...", "data": null}`)이다. 전역 예외 핸들러(`app/presentation/errors.py`) 한곳에서 만든다. 엔드포인트에서 예외를 잡아 오류 응답을 직접 만들지 않는다.
- 예외 클래스는 `app/errors.py`에 두고 상태 코드를 넣지 않는다. 어떤 예외를 어떤 상태 코드·`code`로 답할지는 `app/presentation/errors.py`의 대응표에만 적는다 (`agent-architecture`의 "예외 위치").
- 스트리밍이 시작된 뒤의 예외는 전역 핸들러가 응답을 바꾸지 못한다. `/chat`이 스트리밍 함수 안에서 `except Exception`으로 잡아 `error` 이벤트로 보내고, `code`·`message`는 같은 대응표(`find_error_rule`)에서 가져온다.
- 스트리밍 중 실패의 로그는 `app/presentation/errors.py`의 `log_failure(request, rule, exc, streaming=True)`로 남긴다. 전역 핸들러와 같은 함수라 로그 규칙이 한곳에 있다. 로그 코드를 `routes.py`에 따로 짜지 않는다.
- LLM 호출 실패는 에이전트 쪽에서 `UpstreamError`로 바꿔 던진다 (`langgraph-conventions`의 "LLM 호출 실패 → UpstreamError"). 바꾸지 않으면 `INTERNAL_ERROR`로 나간다.
- 위 표에 없는 `code`를 새로 만들지 않는다. 필요하면 설계 문서 결정 섹션에 적고 사용자에게 확인한다.
- `message`는 사용자에게 보여줄 한국어 안내다. 예외 내용, 스택, 내부 주소를 넣지 않는다. 자세한 내용은 로그에 남긴다 (키·개인정보 제외).
- 안내 문구는 `app/presentation/response/messages.py`에 상수로 모은다. 규칙이나 핸들러 안에 문장을 직접 적지 않는다.
- 가드레일에 막힌 것은 오류가 아니다. 한 번에 응답이면 정상 답으로 안내 문구를 보낸다. 스트리밍 중 출력 검사에 막히면 이미 시작된 응답을 끝내야 해서 `BLOCKED` 이벤트를 쓴다. 알리는 방법은 위 "막혔을 때 알리는 방법"을 따른다.

### app/presentation/errors.py 안의 순서

값과 함수를 묶음별로 모으고 구분 주석(`# ── 이름 ──`)을 단다.

| 순서 | 묶음 | 들어가는 것 |
|---|---|---|
| 1 | 예상하지 못한 오류 (기본값) | `INTERNAL_ERROR_RULE` |
| 2 | 우리가 만든 예외 | `ERROR_RULES` (예외 클래스 → 규칙) |
| 3 | FastAPI가 던지는 예외 | `INVALID_REQUEST_RULE`, `HTTP_CLIENT_ERROR_MESSAGES` |
| 4 | 오류 규칙이 아닌 설정 | `NO_BODY_STATUS_CODES` |
| 5 | 핸들러가 불러 쓰는 함수 | `find_error_rule`, `log_failure`, 응답 만들기 |
| 6 | 핸들러 함수 | `_handle_...` |
| 7 | 핸들러 등록 | `register_exception_handlers` |

- 규칙(`ErrorRule`)은 상태 코드, `code`, 안내 문구 세 가지를 묶은 값이다. 핸들러 함수는 올라온 예외에 맞는 규칙을 골라 응답으로 만든다.
- 예외마다 핸들러 함수를 따로 만들지 않는다. 예외마다 달라지는 것은 규칙 값뿐이다.
- 핸들러 함수를 클래스로 묶지 않는다. 묶는 단위는 파일이다.

### 새 예외를 추가할 때

| 순서 | 파일 | 추가할 것 |
|---|---|---|
| 1 | `app/errors.py` | 예외 클래스 (`AppError`나 그 하위 예외를 물려받는다) |
| 2 | `app/presentation/response/error_code.py` | `code` 값 |
| 3 | `app/presentation/response/messages.py` | 안내 문구 |
| 4 | `app/presentation/errors.py`의 `ERROR_RULES` | 예외 클래스 → `ErrorRule(상태 코드, code, 안내 문구)` |

- 응답이 기존 예외와 같고 로그에서만 구분하면 되는 예외는 1번만 한다. 표에 없는 하위 예외는 가장 가까운 부모의 규칙을 따른다.
- 던지는 쪽(도메인, 서비스, 에이전트, 포트 구현)은 예외 클래스만 쓴다: `raise UpstreamError("상품 조회 실패: id=123")`. 규칙 값이나 `ErrorCode`를 가져다 쓰지 않는다.
- 업무 규칙에 걸려 던지는 예외(예: 취소 불가)는 `app/domain/`에 두고 도구가 잡아 문장으로 바꾼다. 전역 핸들러까지 가지 않으므로 위 네 단계 중 1번도 `app/errors.py`가 아니라 `app/domain/`에 한다.

## 시간 제한

호출하는 쪽(게이트웨이 등)은 정해진 시간까지만 기다린다. 그 시간이 지나면 사용자는 아무 답도 못 받는다. 그래서 **그보다 먼저 끊고 안내한다.**

- 시간 제한 값은 설계 문서 개요의 "시간 제한"을 설정으로 둔다. 코드에 숫자를 적지 않는다.
- 우리 쪽 제한은 호출하는 쪽 제한보다 여유 있게 짧게 잡는다 (예: 2~3초 먼저).
- 시간 제한은 에이전트 흐름(`app/application/agent/`)에서 걸고, 초과하면 `AgentTimeoutError`를 던진다. 기준은 질문 하나의 전체 실행이다.
- 한 번에 응답: 3.11의 `asyncio.timeout(...)`으로 에이전트 실행을 감싼다.
- 스트리밍: 아래 "스트리밍의 시간 제한"을 따른다. `yield`를 `asyncio.timeout` 안에 두지 않는다.
- 호출하는 쪽 제한이 **첫 응답까지**인지 **전체**인지 확인한다. 첫 응답까지라면 SSE는 첫 `token`을 빨리 보내는 것이 중요하다. 확인되지 않았으면 설계 문서에 "확인 필요"로 적고 사용자에게 묻는다.
- 도구가 부르는 외부 시스템에도 각자 시간 제한을 둔다. 하나가 멈춰 전체 시간을 다 쓰지 않게 한다.

### 스트리밍의 시간 제한

답 조각을 내보내는 함수(비동기 제너레이터)에서는 **`yield`를 시간 제한 안에 두지 않는다.** `yield`에서 멈춰 있는 동안 제한이 지나면 취소가 함수 밖에서 걸려, `TimeoutError`로 바뀌지 못하고 연결이 그냥 끊긴다. 사용자는 `TIMEOUT` 안내를 받지 못한다 (Python의 PEP 789가 다루는 문제다).

마감 시각을 한 번 정하고, 다음 조각을 **기다릴 때만** 그 마감으로 제한을 건다.

```python
async def stream_answer(command: ChatCommand, ctx: AgentContext) -> AsyncGenerator[str]:
    deadline = asyncio.get_running_loop().time() + ctx.timeout_seconds
    sentences = _stream_checked_sentences(command, ctx)
    try:
        while True:
            async with asyncio.timeout_at(deadline):      # 기다릴 때만 건다
                sentence = await anext(sentences, None)
            if sentence is None:
                return
            yield sentence                                # 제한 밖에서 내보낸다
    except TimeoutError as e:
        raise AgentTimeoutError(
            f"에이전트 실행 시간 초과: timeout_seconds={ctx.timeout_seconds}"
        ) from e
    finally:
        await sentences.aclose()
```

- 마감 시각은 하나다. 조각마다 제한 시간을 새로 주지 않는다.
- 필수 테스트: 시간 초과가 `TIMEOUT` `error` 이벤트로 끝나는지, 조각이 여러 개여도 전체 시간 기준으로 끊기는지.

## 테스트

엔드포인트 테스트는 `python-testing`을 따른다. 서버를 띄우지 않고 `TestClient`로 `/chat`, `/health`를 부른다. SSE는 받은 본문을 이벤트 단위로 나눠 `token` → `done` 순서를 확인한다.
