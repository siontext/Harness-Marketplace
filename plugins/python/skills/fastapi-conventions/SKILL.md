---
name: fastapi-conventions
description: 에이전트를 앱·다른 서버가 부를 수 있게 여는 FastAPI 창구 규칙 — main.py 시작·종료 조립(lifespan), /chat·/health, pydantic 요청·응답, SSE 스트리밍(기본)과 한 번에 응답(대안), 스트리밍 중 출력 가드레일, 오류 응답 통일, 시간 제한. main.py나 API 코드를 작성하거나 리뷰할 때 참조.
---

# FastAPI Conventions

에이전트는 혼자서는 바깥과 이야기하지 못한다. 호출하는 쪽(앱, 다른 서버)이 `/chat`으로 질문을 보내면 FastAPI가 받아 에이전트에 넘기고 답을 돌려준다. 이 창구는 `main.py` 하나에 둔다.

## main.py — 시작·종료 조립

- 서버가 켜질 때 `lifespan`에서 연결 창구(`build_platform()`)와 에이전트를 **한 번** 만든다. 요청마다 만들지 않는다.
- 만든 것은 `app.state`에 둔다. 엔드포인트는 `request.app.state`에서 꺼내 쓴다.
- 서버가 꺼질 때 연결(Redis, DB, HTTP 클라이언트)을 닫는다.
- 연결 창구를 불러오지 못하면 서버가 뜨지 않게 그대로 오류를 낸다 (`agent-architecture`).

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    platform = build_platform()
    app.state.ctx = build_agent_context(platform)
    yield
    await platform.aclose()


app = FastAPI(lifespan=lifespan)
```

- `@app.on_event("startup")`은 쓰지 않는다 (예전 방식).
- 엔드포인트는 `async def`로 쓴다. 안에서 동기 블로킹 호출 금지 (`python-style`).

## 주소

| Method | Path | 하는 일 |
|---|---|---|
| POST | `/chat` | 질문을 받아 답한다 |
| GET | `/health` | 서버가 살아 있는지 알려 준다. `{"status": "ok"}` |

- `/health`는 LLM이나 DB를 부르지 않는다. 서버 프로세스가 응답하는지만 본다.
- 주소를 더 만들 때는 설계 문서에 적힌 경우만.

## 요청·응답 모양

pydantic 모델로 정한다. 필드 설명은 한국어 `Field(description=...)`.

```python
class ChatRequest(BaseModel):
    conversation_id: str = Field(min_length=1, description="대화 id. 같은 대화는 같은 값")
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH, description="사용자 질문")
```

- 요청 모델에서 길이·형식을 검사한다. 검사 실패는 FastAPI가 422로 돌려준다.
- 호출하는 쪽과 다른 모양이 필요하면 설계 문서 개요에 적고 그에 맞춘다.

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

- `StreamingResponse(..., media_type="text/event-stream")`로 보낸다. 헤더에 `Cache-Control: no-cache`를 넣는다.
- `data`는 JSON 한 줄로 쓴다 (`json.dumps(..., ensure_ascii=False)`). 줄바꿈이 들어간 글자를 그대로 쓰면 이벤트가 깨진다.
- 이벤트 하나는 빈 줄(`\n\n`)로 끝낸다.
- 스트리밍이 시작된 뒤에는 HTTP 상태 코드를 바꿀 수 없다. 실패는 `error` 이벤트로 알린다.
- 대화 기억·기록 저장은 `done`을 보내기 직전에 한다.

### 스트리밍 중 출력 가드레일

이미 보낸 글자는 되돌릴 수 없다. 그래서 **검사하고 나서 보낸다.**

- LLM 조각을 문장 단위로 모아 출력 가드레일을 거친 뒤 `token`으로 보낸다.
- 운영 플랫폼 가드레일이 스트리밍 검사(조각을 이어서 검사하는 세션)를 제공하면 그것을 쓴다.
- 검사에서 막히면 그 자리에서 `error` 이벤트(`code`: `BLOCKED`, `message`: 안내 문구)를 보내고 끝낸다. 막힌 내용은 대화 기록에 "차단됨"으로 남긴다.
- 입력 가드레일은 스트리밍과 상관없이 LLM을 부르기 전에 한 번 한다.

### 한 번에 응답 (대안)

```python
class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
```

호출하는 쪽이 SSE를 받지 못하면 `/chat`이 `ChatResponse`를 JSON으로 돌려주게 바꾼다. 에이전트 코드(`app/agent/`)는 그대로 두고 `main.py`의 엔드포인트만 바꾼다. 그래서 에이전트 쪽에는 스트리밍용 함수와 한 번에 답하는 함수를 함께 둔다.

## 오류 응답 통일

| 상황 | 상태 코드 | code |
|---|---|---|
| 요청 형식 오류 | 422 | `INVALID_REQUEST` |
| 입력 가드레일에 막힘 | 200 (안내 문구가 답) | — |
| 출력 가드레일에 막힘 | 200 (안내 문구가 답). 스트리밍 중이면 `error` 이벤트 | `BLOCKED` |
| 시간 초과 | 504 (스트리밍 중이면 `error` 이벤트) | `TIMEOUT` |
| LLM·외부 시스템 오류 | 502 (스트리밍 중이면 `error` 이벤트) | `UPSTREAM_ERROR` |
| 그 밖의 오류 | 500 | `INTERNAL_ERROR` |

- 오류 본문은 항상 `{"code": "...", "message": "..."}` 모양이다. `exception_handler`로 한곳에서 만든다.
- 위 표에 없는 `code`를 새로 만들지 않는다. 필요하면 설계 문서 결정 섹션에 적고 사용자에게 확인한다.
- `message`는 사용자에게 보여줄 한국어 안내다. 예외 내용, 스택, 내부 주소를 넣지 않는다. 자세한 내용은 로그에 남긴다 (키·개인정보 제외).
- 가드레일에 막힌 것은 오류가 아니다. 한 번에 응답이면 정상 답으로 안내 문구를 보낸다. 스트리밍 중 출력 검사에 막히면 이미 시작된 응답을 끝내야 해서 `BLOCKED` 이벤트를 쓴다.

## 시간 제한

호출하는 쪽(게이트웨이 등)은 정해진 시간까지만 기다린다. 그 시간이 지나면 사용자는 아무 답도 못 받는다. 그래서 **그보다 먼저 끊고 안내한다.**

- 시간 제한 값은 설계 문서 개요의 "시간 제한"을 설정으로 둔다. 코드에 숫자를 적지 않는다.
- 우리 쪽 제한은 호출하는 쪽 제한보다 여유 있게 짧게 잡는다 (예: 2~3초 먼저).
- 3.11의 `asyncio.timeout(...)`으로 에이전트 실행을 감싼다. 초과하면 `TIMEOUT` 안내를 보낸다.
- 호출하는 쪽 제한이 **첫 응답까지**인지 **전체**인지 확인한다. 첫 응답까지라면 SSE는 첫 `token`을 빨리 보내는 것이 중요하다. 확인되지 않았으면 설계 문서에 "확인 필요"로 적고 사용자에게 묻는다.
- 도구가 부르는 외부 시스템에도 각자 시간 제한을 둔다. 하나가 멈춰 전체 시간을 다 쓰지 않게 한다.

## 테스트

엔드포인트 테스트는 `python-testing`을 따른다. 서버를 띄우지 않고 `TestClient`로 `/chat`, `/health`를 부른다. SSE는 받은 본문을 이벤트 단위로 나눠 `token` → `done` 순서를 확인한다.
