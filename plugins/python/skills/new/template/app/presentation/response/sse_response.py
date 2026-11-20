"""스트리밍(/chat) 응답 만들기. 유스케이스가 내놓은 문장 흐름을 SSE 응답으로 바꾼다.

컨트롤러는 이 함수에 문장 흐름을 넘기기만 한다. 이벤트 모양(SseEvent)과
스트리밍 중 실패를 error 이벤트로 바꾸는 일은 여기서 한다. 스트리밍이 시작된 뒤에는
전역 예외 핸들러가 응답을 바꾸지 못하기 때문이다.
"""

import logging
from collections.abc import AsyncGenerator, AsyncIterator

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.application.agent.errors import InputBlockedError, OutputBlockedError
from app.presentation.errors import find_error_rule, log_failure
from app.presentation.response import messages
from app.presentation.response.error_code import ErrorCode
from app.presentation.response.sse_event import SseEvent

logger = logging.getLogger(__name__)

SSE_MEDIA_TYPE = "text/event-stream"
SSE_HEADERS = {"Cache-Control": "no-cache"}


def sse_response(
    sentences: AsyncIterator[str], conversation_id: str, request: Request
) -> StreamingResponse:
    """문장 흐름을 token 이벤트들 → done으로 보내는 SSE 응답을 만든다.

    실패하면 error 이벤트 하나로 끝난다.

    Args:
        sentences: 유스케이스가 내놓는 문장 흐름.
        conversation_id: done 이벤트에 돌려줄 대화 id.
        request: 들어온 요청. 실패 로그에 요청 방식과 경로를 남긴다.

    Returns:
        text/event-stream 응답.
    """
    return StreamingResponse(
        _stream_events(sentences, conversation_id, request),
        media_type=SSE_MEDIA_TYPE,
        headers=SSE_HEADERS,
    )


async def _stream_events(
    sentences: AsyncIterator[str], conversation_id: str, request: Request
) -> AsyncGenerator[str]:
    """문장을 token 이벤트로 바꾸고, 끝나면 done, 실패하면 error를 보낸다."""
    try:
        async for sentence in sentences:
            yield SseEvent.token(sentence).encode()
    except InputBlockedError as e:
        # 질문이 막힌 것도 오류가 아니다. 답을 시작하기 전이라 안내 문구를
        # 정상 답으로 보내고 아래 done으로 끝낸다.
        logger.warning("입력 가드레일 차단: %s %s", request.method, request.url.path)
        yield SseEvent.token(e.guard_message or messages.INPUT_BLOCKED).encode()
    except OutputBlockedError as e:
        # 막힌 것은 오류가 아니다. 막힌 내용은 남기지 않고 사실만 남긴다.
        logger.warning("출력 가드레일 차단: %s %s", request.method, request.url.path)
        message = e.guard_message or messages.BLOCKED
        yield SseEvent.error(ErrorCode.BLOCKED, message).encode()
        return
    # 스트리밍이 시작된 뒤의 마지막 경계다. 전역 핸들러와 같은 대응표로 답한다.
    except Exception as exc:
        rule = find_error_rule(exc)
        log_failure(request, rule, exc, streaming=True)
        yield SseEvent.error(rule.code, rule.message).encode()
        return
    yield SseEvent.done(conversation_id).encode()
