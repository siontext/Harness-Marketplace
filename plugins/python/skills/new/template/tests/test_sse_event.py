"""스트리밍 이벤트 틀(SseEvent) 단위 테스트."""

import json

from app.api.response.error_code import ErrorCode
from app.api.response.sse_event import SseEvent


def test_token_이벤트는_event_줄과_data_줄과_빈_줄로_내보낸다() -> None:
    # When
    encoded = SseEvent.token("주문하시면").encode()

    # Then
    assert encoded == 'event: token\ndata: {"text": "주문하시면"}\n\n'


def test_줄바꿈이_든_조각도_data는_한_줄이다() -> None:
    # When
    encoded = SseEvent.token("첫 줄\n둘째 줄").encode()

    # Then
    data_line = encoded.split("\n")[1]
    assert encoded.count("\n") == 3
    assert json.loads(data_line.removeprefix("data: ")) == {"text": "첫 줄\n둘째 줄"}


def test_done_이벤트는_대화_id를_담는다() -> None:
    # When
    encoded = SseEvent.done("c-123").encode()

    # Then
    assert encoded == 'event: done\ndata: {"conversation_id": "c-123"}\n\n'


def test_error_이벤트는_실패_응답과_같은_code와_message를_담는다() -> None:
    # When
    encoded = SseEvent.error(ErrorCode.UPSTREAM_ERROR, "답하지 못했습니다.").encode()

    # Then
    assert encoded == (
        "event: error\n"
        'data: {"code": "UPSTREAM_ERROR", "message": "답하지 못했습니다."}\n\n'
    )
