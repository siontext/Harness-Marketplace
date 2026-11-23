---
name: fastapi-conventions
description: 에이전트를 앱·다른 서버가 부를 수 있게 여는 FastAPI 창구 규칙 — main.py(lifespan)와 app/presentation 파일 배치(routes·schemas·errors·response), /chat·/health, pydantic 요청·응답, 공통 응답 틀(ApiResponse·SseEvent·SseResponse), 전역 예외 핸들러(GlobalExceptionHandler)와 main.py 등록, 엔드포인트는 세 단계만, SSE 스트리밍(기본)과 한 번에 응답(대안), 스트리밍 중 출력 가드레일, 오류 응답 통일, 시간 제한. main.py나 app/presentation 코드를 작성하거나 리뷰할 때 참조.
---

# FastAPI Conventions

에이전트는 혼자서는 바깥과 이야기하지 못한다. 호출하는 쪽(앱, 다른 서버)이 `/chat`으로 질문을 보내면 FastAPI가 받아 에이전트에 넘기고 답을 돌려준다. FastAPI를 아는 코드는 `main.py`와 `app/presentation/`에만 둔다.

## 파일 배치

| 파일 | 두는 것 |
|---|---|
| `main.py` | 부트스트랩 — `FastAPI` 앱 만들기, `lifespan`, 전역 예외 핸들러 등록(어떤 예외를 어느 메서드가 잡는지), 라우터 붙이기. 엔드포인트나 모델을 직접 적지 않는다 |
| `app/presentation/routes.py` | 엔드포인트 (`APIRouter`) |
| `app/presentation/schemas.py` | 엔드포인트별 요청·응답 내용 (`ChatRequest`, `HealthStatus` 등). 공통 응답 틀은 두지 않는다 |
| `app/presentation/errors.py` | 오류 규칙(`ErrorRule`), 예외 → 규칙 대응표, 규칙 찾기(`ErrorRuleBook`), 실패 로그(`FailureLogger`), 전역 예외 핸들러(`GlobalExceptionHandler`) |
| `app/presentation/response/api_response.py` | `ApiResponse` — JSON 응답의 공통 틀 |
| `app/presentation/response/sse_event.py` | `SseEvent` — 스트리밍 이벤트 하나의 공통 틀 |
| `app/presentation/response/sse_response.py` | `SseResponse` — 문장 흐름을 SSE 응답(`token`들 → `done`, 실패하면 `error`)으로 보내는 `StreamingResponse`. 뼈대에 있다 |
| `app/presentation/response/error_code.py` | `ErrorCode` — 오류 응답의 `code` 값 |
| `app/presentation/response/messages.py` | 사용자에게 보여줄 안내 문구 |

- `app/presentation`은 `app/application`을 부르고, 그 반대는 금지다. `app/infrastructure`는 import하지 않는다 (`agent-architecture`).
- 응답 틀은 종류마다 `app/presentation/response/`에 파일 하나로 둔다. 목록 조회가 생기면 `page_response.py`(`PageResponse`)를 더한다.

### 엔드포인트는 세 단계만

엔드포인트 함수는 **요청 → Command, 유스케이스 부르기, 응답 틀에 담기** 세 단계만 한다. 응답 모양을 만드는 일과 오류 처리는 응답 틀(`app/presentation/response/`)과 전역 핸들러가 맡는다.

```python
@router.post("/chat")
async def chat(body: ChatRequest, request: Request) -> SseResponse:
    command = ChatCommand(conversation_id=body.conversation_id, message=body.message)
    chat: ChatUseCase = request.app.state.chat
    return SseResponse(chat.stream_answer(command), command.conversation_id, request)
```

- 엔드포인트가 아는 `application`의 것은 Command와 유스케이스(인터페이스)뿐이다.
- 엔드포인트는 FastAPI가 함수 모양을 요구하므로 함수로 둔다 (`python-style`의 "클래스가 기본"의 예외).
- SSE 이벤트 글자 만들기, 스트리밍 중 `try/except`, 실패 로그를 엔드포인트에 직접 적지 않는다. `SseResponse`가 한다.
- `SseResponse`는 뼈대의 것을 쓴다. 새로 만들지 않는다.
- 그 밖에 `app/presentation/` 안에 파일을 더 만들 때는 설계 문서에 적힌 경우만.

## main.py — 시작·종료 조립

- `main.py`는 부트스트랩이다. 무엇이 무엇에 연결됐는지(서버 시작 조립, 예외 → 핸들러 메서드, 라우터)를 이 파일에서 다 보이게 한다.
- 서버가 켜질 때 `lifespan`에서 설정(`Settings.from_env()`)과 연결 창구(`Platform.from_settings()`)를 만들고 `app/container.py`의 `Container`로 에이전트를 **한 번** 만든다. 요청마다 만들지 않는다.
- 만든 것은 `app.state`에 둔다. 엔드포인트는 `request.app.state`에서 꺼내 쓴다.
- 서버가 꺼질 때 연결(Redis, DB, HTTP 클라이언트)을 닫는다.
- 연결 창구를 불러오지 못하면 서버가 뜨지 않게 그대로 오류를 낸다 (`agent-architecture`).

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings.from_env()
    platform = Platform.from_settings(settings)
    app.state.chat = Container(platform, settings).build_chat_service()
    yield
    await platform.aclose()


app = FastAPI(lifespan=lifespan)

# ── 전역 예외 핸들러 등록 (어떤 예외를 어느 메서드가 잡는지) ──────────────
handler = GlobalExceptionHandler()
app.exception_handler(AppError)(handler.handle_app_error)
app.exception_handler(RequestValidationError)(handler.handle_validation_error)
app.exception_handler(StarletteHTTPException)(handler.handle_http_exception)
app.exception_handler(Exception)(handler.handle_unexpected)

# ── 엔드포인트 ──────────────────────────────────────────────────────────
app.include_router(router)
```

- **전역 예외 핸들러는 `main.py`에서 등록한다.** 등록은 "이 핸들러를 쓰겠다"는 연결이라 부트스트랩의 일이다. 핸들러 메서드 자체는 `app/presentation/errors.py`의 `GlobalExceptionHandler`에 둔다 (아래 "app/presentation/errors.py 안의 순서").
- 등록은 뼈대의 네 줄을 그대로 쓴다. `AppError`를 `Exception`과 따로 등록해야 응답 뒤에 예외가 다시 던져지지 않는다. 404·405는 Starlette의 `HTTPException`으로 등록해야 잡힌다.
- 핸들러는 `app.exception_handler(<예외>)(<메서드>)`로 등록한다. `app.add_exception_handler`는 메서드의 예외 인자 타입 때문에 타입 검사에 걸린다.

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
# app/presentation/schemas.py
# 질문 하나의 최대 글자 수. 설계 문서 개요에 다른 값이 없으면 1000.
MAX_MESSAGE_LENGTH = 1000


class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=1, description="대화 id. 같은 대화는 같은 값")
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH, description="사용자 질문")
```

- 요청 모델에서 길이·형식을 검사한다. 검사 실패는 FastAPI가 422로 돌려준다.
- `MAX_MESSAGE_LENGTH`는 `app/presentation/schemas.py` 위쪽에 상수로 둔다. 호출하는 쪽이 다른 값을 쓰면 설계 문서 개요에 적고 그 값을 쓴다.
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
- `SseResponse`로 보낸다. `StreamingResponse`를 물려받아 `text/event-stream`과 `Cache-Control: no-cache` 헤더를 넣는다.
- `data`는 JSON 한 줄이고 이벤트 하나는 빈 줄(`\n\n`)로 끝난다. 줄바꿈이 들어간 글자를 그대로 쓰면 이벤트가 깨진다. `encode()`가 이 모양을 맞춘다.
- 스트리밍이 시작된 뒤에는 HTTP 상태 코드를 바꿀 수 없다. 실패는 `error` 이벤트로 알린다.
- 대화 기억·기록 저장은 `done`을 보내기 직전에 한다.

### 스트리밍 중 출력 가드레일

이미 보낸 글자는 되돌릴 수 없다. 그래서 **검사하고 나서 보낸다.**

- LLM 조각을 문장 단위로 모아 출력 가드레일을 거친 뒤 `token`으로 보낸다. 가드레일이 돌려준 문장(가려졌을 수 있다)을 보낸다.
- 조각을 문장으로 모으는 일은 뼈대의 `SentenceSplitter`(`app/application/common/sentences.py`)가 한다. **직접 짜지 않는다.** 문장이 끝나는 자리의 기준은 아래와 같고, 마지막에 남은 글자도 하나의 문장으로 내보낸다.

| 끊는 자리 | 예 |
|---|---|
| 마침표·물음표·느낌표(`. ! ?` 와 `。！？`) 뒤에 공백이 올 때 | `...했습니다. 다음은` |
| 줄이 바뀔 때 | 목록의 각 줄 |
| 끊지 않는다: 점 뒤에 공백이 없을 때 | `3.5일`, `a@b.com` |
| 끊지 않는다: 숫자 바로 뒤의 점 | `1. 첫째` (목록 번호) |

- 문장이 끝나지 않았는데 길다고 중간에서 끊어 보내지 않는다. 가려야 할 값이 둘로 나뉘어 검사를 빠져나갈 수 있다.
- 운영 플랫폼 가드레일이 스트리밍 검사(조각을 이어서 검사하는 세션)를 제공하면 그것을 쓴다.
- 검사에서 막히면 그 자리에서 `error` 이벤트(`code`: `BLOCKED`, `message`: 안내 문구)를 보내고 끝낸다. 막힌 내용은 대화 기록에 "차단됨"으로 남긴다.
- 입력 가드레일은 스트리밍과 상관없이 LLM을 부르기 전에 한 번 한다.

#### 막혔을 때 알리는 방법

| 막힌 곳 | 채팅 서비스(`application`)가 하는 일 | `/chat`(`SseResponse`)이 보내는 것 |
|---|---|---|
| 입력 | LLM을 부르지 않고 `InputBlockedError`를 던진다 | `token`(안내 문구) → `done`. 답을 시작하기 전이라 정상 답처럼 보낸다 |
| 출력 | `OutputBlockedError`를 던진다. 더 진행할 수 없으므로 무시할 수 없게 한다 | `error` · `BLOCKED` |

```python
# app/presentation/response/sse_response.py의 SseResponse._stream_events (뼈대에 있다)
try:
    async for sentence in sentences:          # 유스케이스가 내놓은 문장 흐름
        yield SseEvent.token(sentence).encode()
except InputBlockedError as e:         # 의도된 결과: 안내 문구를 답으로 보내고 아래 done으로
    logger.warning("입력 가드레일 차단: %s %s", request.method, request.url.path)
    yield SseEvent.token(e.guard_message or messages.INPUT_BLOCKED).encode()
except OutputBlockedError as e:        # 의도된 결과: 이름을 적어 따로 잡는다
    logger.warning("출력 가드레일 차단: %s %s", request.method, request.url.path)
    yield SseEvent.error(ErrorCode.BLOCKED, e.guard_message or messages.BLOCKED).encode()
    return
# 스트리밍이 시작된 뒤의 마지막 경계다. 전역 핸들러와 같은 대응표로 답한다.
except Exception as exc:
    rule = self._rules.find(exc)                       # ErrorRuleBook
    self._failures.log(request, rule, exc, streaming=True)  # FailureLogger
    yield SseEvent.error(rule.code, rule.message).encode()
    return
yield SseEvent.done(conversation_id).encode()
```

- `InputBlockedError`·`OutputBlockedError`는 `app/application/agent/errors.py`(뼈대에 있다)에 있고 가드레일이 준 안내 문구를 담는다. **문구가 비어 있으면 `SseResponse`가 `messages.INPUT_BLOCKED`·`messages.BLOCKED`를 쓴다.** 운영 플랫폼 가드레일이 문구 없이 막을 수 있어서, 채팅 서비스가 문구를 직접 내보내면 빈 답이 나갈 수 있다.
- **두 예외를 오류 대응표(`ERROR_RULES`)에 넣지 않는다.** 막힌 것은 오류가 아니라서 상태 코드가 없다. LLM 실패 같은 오류와 같은 `except`에서 처리하지 않는다.
- 로그에는 막혔다는 사실만 남기고 막힌 내용은 남기지 않는다.
- 한 번에 응답 방식에서는 엔드포인트가 두 예외를 잡아 안내 문구(비면 기본 문구)를 정상 답(200)으로 돌려준다.

### 한 번에 응답 (대안)

```python
class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
```

호출하는 쪽이 SSE를 받지 못하면 `/chat`이 `ApiResponse[ChatResponse]`를 JSON으로 돌려주게 바꾼다. 이때 `ChatUseCase`·`ChatService`에 한 번에 답하는 메서드(`answer`)를 더하고 `app/presentation/routes.py`의 엔드포인트를 바꾼다. 답 만들기 어댑터, 도구, 서비스는 그대로다.

- 설계 문서의 응답 방식에 해당하는 메서드만 만든다. 쓰지 않는 방식의 메서드를 미리 만들어 두지 않는다.

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
- 예외 클래스는 `app/common/errors.py`에 두고 상태 코드를 넣지 않는다. 어떤 예외를 어떤 상태 코드·`code`로 답할지는 `app/presentation/errors.py`의 대응표에만 적는다 (`agent-architecture`의 "예외 위치").
- 스트리밍이 시작된 뒤의 예외는 전역 핸들러가 응답을 바꾸지 못한다. `SseResponse`가 `except Exception`으로 잡아 `error` 이벤트로 보내고, `code`·`message`는 같은 대응표(`ErrorRuleBook.find`)에서 가져온다.
- 스트리밍 중 실패의 로그는 `app/presentation/errors.py`의 `FailureLogger.log(request, rule, exc, streaming=True)`로 남긴다. 전역 핸들러와 같은 클래스라 로그 규칙이 한곳에 있다. 로그 코드를 `routes.py`에 따로 짜지 않는다.
- LLM 호출 실패는 에이전트 쪽에서 `UpstreamError`로 바꿔 던진다 (`langgraph-conventions`의 "LLM 호출 실패 → UpstreamError"). 바꾸지 않으면 `INTERNAL_ERROR`로 나간다.
- 도구가 부르는 외부 시스템(DB, 외부 API)의 고장도 같다. 포트 구현이 `UpstreamError`를 던지고, 도구는 잡지 않는다. 그래서 `UPSTREAM_ERROR`로 끝난다 (`agent-architecture`의 "예외 위치").
- 위 표에 없는 `code`를 새로 만들지 않는다. 필요하면 설계 문서 결정 섹션에 적고 사용자에게 확인한다.
- `message`는 사용자에게 보여줄 한국어 안내다. 예외 내용, 스택, 내부 주소를 넣지 않는다. 자세한 내용은 로그에 남긴다 (키·개인정보 제외).
- 안내 문구는 `app/presentation/response/messages.py`에 상수로 모은다. 규칙이나 핸들러 안에 문장을 직접 적지 않는다.
- 가드레일에 막힌 것은 오류가 아니다. 한 번에 응답이면 정상 답으로 안내 문구를 보낸다. 스트리밍 중 출력 검사에 막히면 이미 시작된 응답을 끝내야 해서 `BLOCKED` 이벤트를 쓴다. 알리는 방법은 위 "막혔을 때 알리는 방법"을 따른다.

### app/presentation/errors.py 안의 순서

규칙 값(대응표)을 묶음별로 모아 구분 주석(`# ── 이름 ──`)을 달고, 그 아래에 클래스를 둔다.

| 순서 | 묶음 | 들어가는 것 |
|---|---|---|
| 1 | 오류 규칙 | `ErrorRule` (상태 코드·`code`·안내 문구 값, `to_response()`), `NO_BODY_STATUS_CODES` |
| 2 | 예상하지 못한 오류 (기본값) | `INTERNAL_ERROR_RULE` |
| 3 | 우리가 만든 예외 | `ERROR_RULES` (예외 클래스 → 규칙) |
| 4 | FastAPI가 던지는 예외 | `INVALID_REQUEST_RULE`, `HTTP_CLIENT_ERROR_MESSAGES` |
| 5 | 규칙 찾기 | `ErrorRuleBook` (`find`, `find_for_status`) |
| 6 | 실패 로그 | `FailureLogger` (`log`, `log_invalid_request`) |
| 7 | 전역 예외 핸들러 | `GlobalExceptionHandler` — 예외 종류마다 메서드 하나 |

| `GlobalExceptionHandler` 메서드 | 맡는 예외 | 답 |
|---|---|---|
| `handle_app_error` | 우리가 만든 예외 (`AppError` 하위) | 대응표의 규칙 (504, 502, 500) |
| `handle_validation_error` | 요청 형식 오류 (`RequestValidationError`) | 422 · `INVALID_REQUEST` |
| `handle_http_exception` | 없는 주소·틀린 방식 등 (Starlette `HTTPException`) | 원래 상태 코드와 헤더 그대로 |
| `handle_unexpected` | 그 밖의 모든 예외 | 500 · `INTERNAL_ERROR` |

- **핸들러는 `GlobalExceptionHandler` 클래스 하나에 두고, 예외 종류 하나에 메서드 하나를 둔다.** 메서드 이름과 독스트링으로 어떤 예외를 맡는지 보인다 (Kotlin의 `@RestControllerAdvice` `GlobalExceptionHandler`와 같은 모양). 어느 메서드가 어떤 예외를 잡는지는 `main.py`에서 등록한다.
- 메서드에 상태 코드·`code`·안내 문구를 적지 않는다. 규칙은 대응표에서 찾고(`ErrorRuleBook`), 응답은 규칙이 만든다(`ErrorRule.to_response()`).
- 우리가 만든 예외는 `handle_app_error` 하나가 맡는다. 예외가 늘어도 대응표에 한 줄만 더한다. 응답 말고 다른 일(알림 등)을 해야 하는 예외가 생기면 그 예외의 메서드를 더하고 `main.py`에 등록한다.
- `ErrorRuleBook`·`FailureLogger`는 설정 값도 바꿔 끼울 구현도 없어서 `GlobalExceptionHandler`와 `SseResponse`가 생성자 안에서 만든다.

### 새 예외를 추가할 때

| 순서 | 파일 | 추가할 것 |
|---|---|---|
| 1 | `app/common/errors.py` | 예외 클래스 (`AppError`나 그 하위 예외를 물려받는다) |
| 2 | `app/presentation/response/error_code.py` | `code` 값 |
| 3 | `app/presentation/response/messages.py` | 안내 문구 |
| 4 | `app/presentation/errors.py`의 `ERROR_RULES` | 예외 클래스 → `ErrorRule(상태 코드, code, 안내 문구)` |

- 응답이 기존 예외와 같고 로그에서만 구분하면 되는 예외는 1번만 한다. 표에 없는 하위 예외는 가장 가까운 부모의 규칙을 따른다.
- 던지는 쪽(도메인, 서비스, 에이전트, 포트 구현)은 예외 클래스만 쓴다: `raise UpstreamError("상품 조회 실패: id=123")`. 규칙 값이나 `ErrorCode`를 가져다 쓰지 않는다.
- 업무 예외(대상 없음, 규칙에 걸림)는 `app/domain/<기능>/`에 두고 도구가 잡아 문장으로 바꾼다. 전역 핸들러까지 가지 않으므로 예외 클래스만 `app/domain/<기능>/`에 만들고 2~4번은 하지 않는다.

## 시간 제한

호출하는 쪽(게이트웨이 등)은 정해진 시간까지만 기다린다. 그 시간이 지나면 사용자는 아무 답도 못 받는다. 그래서 **그보다 먼저 끊고 안내한다.**

- 설계 문서 개요의 "시간 제한"에는 두 값을 적는다: 호출하는 쪽이 기다려 주는 시간과 우리 쪽 제한. **우리 쪽 제한을 환경 변수 `AGENT_TIMEOUT_SECONDS`로 둔다.** 뼈대의 `Settings.agent_timeout_seconds`가 읽는다 (비우면 30초). 코드에 숫자를 적지 않는다.
- 우리 쪽 제한은 호출하는 쪽 제한보다 여유 있게 짧게 잡는다 (예: 2~3초 먼저). 호출하는 쪽 제한이 없거나 모르면 기본값 30초를 쓰고 "확인 필요"로 적는다.
- 시간 제한은 에이전트 흐름(`app/application/agent/`)에서 걸고, 초과하면 `AgentTimeoutError`를 던진다. 기준은 질문 하나의 전체 실행이다.
- 한 번에 응답: 3.11의 `asyncio.timeout(...)`으로 에이전트 실행을 감싼다.
- 스트리밍: 아래 "스트리밍의 시간 제한"을 따른다. `yield`를 `asyncio.timeout` 안에 두지 않는다.
- 호출하는 쪽 제한이 **첫 응답까지**인지 **전체**인지 확인한다. 첫 응답까지라면 SSE는 첫 `token`을 빨리 보내는 것이 중요하다. 확인되지 않았으면 설계 문서에 "확인 필요"로 적고 사용자에게 묻는다.
- 도구가 부르는 외부 시스템에도 각자 시간 제한을 둔다. 하나가 멈춰 전체 시간을 다 쓰지 않게 한다.

### 스트리밍의 시간 제한

답 조각을 내보내는 비동기 제너레이터에서는 **`yield`를 시간 제한 안에 두지 않는다.** `yield`에서 멈춰 있는 동안 제한이 지나면 취소가 함수 밖에서 걸려, `TimeoutError`로 바뀌지 못하고 연결이 그냥 끊긴다. 사용자는 `TIMEOUT` 안내를 받지 못한다 (Python의 PEP 789가 다루는 문제다).

마감 시각을 한 번 정하고, 다음 조각을 **기다릴 때만** 그 마감으로 제한을 건다. 이 방식은 뼈대의 `TimeLimit`(`app/application/common/time_limit.py`)에 들어 있다. **직접 짜지 않고 `TimeLimit.apply()`로 감싼다.**

```python
# app/application/agent/service.py — ChatService
def stream_answer(self, command: ChatCommand) -> AsyncIterator[str]:
    sentences = self._checked_sentences(command)
    return self._time_limit.apply(sentences)    # 넘으면 AgentTimeoutError
```

- 마감 시각은 하나다. 조각마다 제한 시간을 새로 주지 않는다.
- 필수 테스트: 시간 초과가 `TIMEOUT` `error` 이벤트로 끝나는지, 조각이 여러 개여도 전체 시간 기준으로 끊기는지.

## 테스트

엔드포인트 테스트는 `python-testing`을 따른다. 서버를 띄우지 않고 `TestClient`로 `/chat`, `/health`를 부른다. SSE는 받은 본문을 이벤트 단위로 나눠 `token` → `done` 순서를 확인한다. `lifespan`은 `python-testing`의 "서버 시작(lifespan) 테스트"로 따로 확인한다.
