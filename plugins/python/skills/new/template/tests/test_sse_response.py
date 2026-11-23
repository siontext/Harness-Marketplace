"""SSE 응답 만들기 테스트. 문장 흐름을 token·done·error 이벤트로 바꾸는지 확인한다."""

import json
import logging
from collections.abc import AsyncIterator, Callable

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.application.agent.errors import InputBlockedError, OutputBlockedError
from app.common.errors import UpstreamError
from app.presentation.response.sse_response import SseResponse

FAILURE_LOGGER = "app.presentation.exception.failure_logger"
SSE_LOGGER = "app.presentation.response.sse_response"

Event = tuple[str, dict[str, str]]


def _client(sentences: Callable[[], AsyncIterator[str]]) -> TestClient:
    """문장 흐름 하나를 SseResponse로 돌려주는 엔드포인트만 있는 앱."""
    app = FastAPI()

    @app.post("/stream")
    async def stream(request: Request) -> SseResponse:
        return SseResponse(sentences(), "c-1", request)

    return TestClient(app)


def _events(client: TestClient) -> list[Event]:
    response = client.post("/stream")
    assert response.headers["content-type"].startswith("text/event-stream")
    events = []
    for block in response.text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def _sentences(
    *texts: str, then: Exception | None = None
) -> Callable[[], AsyncIterator[str]]:
    async def generate() -> AsyncIterator[str]:
        for text in texts:
            yield text
        if then is not None:
            raise then

    return generate


def test_문장을_token으로_보내고_done으로_끝낸다() -> None:
    # When
    events = _events(_client(_sentences("첫 문장. ", "둘째 문장.")))

    # Then
    assert events == [
        ("token", {"text": "첫 문장. "}),
        ("token", {"text": "둘째 문장."}),
        ("done", {"conversation_id": "c-1"}),
    ]


@pytest.mark.parametrize(
    ("guard_message", "expected"),
    [
        ("가드레일 문구", "가드레일 문구"),
        ("", "답변드릴 수 없는 질문입니다. 다른 질문을 해 주세요."),
    ],
    ids=["가드레일_문구", "비면_기본_문구"],
)
def test_입력이_막히면_안내_문구를_token으로_보내고_done으로_끝낸다(
    caplog: pytest.LogCaptureFixture, guard_message: str, expected: str
) -> None:
    # Given
    client = _client(_sentences(then=InputBlockedError(guard_message)))

    # When
    with caplog.at_level(logging.WARNING, logger=SSE_LOGGER):
        events = _events(client)

    # Then
    assert events == [
        ("token", {"text": expected}),
        ("done", {"conversation_id": "c-1"}),
    ]
    assert [r.getMessage() for r in caplog.records if r.name == SSE_LOGGER] == [
        "입력 가드레일 차단: POST /stream"
    ]


@pytest.mark.parametrize(
    ("guard_message", "expected"),
    [
        ("가드레일 문구", "가드레일 문구"),
        ("", "보여 드릴 수 없는 내용이 있어 답변을 중단했습니다."),
    ],
    ids=["가드레일_문구", "비면_기본_문구"],
)
def test_출력이_막히면_BLOCKED_error로_끝내고_막힌_사실만_로그에_남긴다(
    caplog: pytest.LogCaptureFixture, guard_message: str, expected: str
) -> None:
    # Given
    client = _client(_sentences("첫 문장. ", then=OutputBlockedError(guard_message)))

    # When
    with caplog.at_level(logging.WARNING, logger=SSE_LOGGER):
        events = _events(client)

    # Then
    assert events == [
        ("token", {"text": "첫 문장. "}),
        ("error", {"code": "BLOCKED", "message": expected}),
    ]
    assert [r.getMessage() for r in caplog.records if r.name == SSE_LOGGER] == [
        "출력 가드레일 차단: POST /stream"
    ]


def test_그_밖의_실패는_오류_대응표로_error를_보내고_스트리밍_중_실패로_남긴다(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    client = _client(_sentences(then=UpstreamError("LLM 호출 실패: ConnectError")))

    # When
    with caplog.at_level(logging.WARNING, logger=FAILURE_LOGGER):
        events = _events(client)

    # Then
    (event,) = events
    assert event[0] == "error"
    assert event[1]["code"] == "UPSTREAM_ERROR"
    (record,) = [r for r in caplog.records if r.name == FAILURE_LOGGER]
    assert "스트리밍 중: error 이벤트로 응답" in record.getMessage()
