"""실패 로그 테스트. 전역 핸들러를 거치지 않는 스트리밍 중 실패의 로그를 확인한다.

전역 핸들러를 거치는 실패의 로그는 test_global_exception_handler.py가 확인한다.
"""

import logging

import pytest
from fastapi import Request

from app.common.errors import UpstreamError
from app.presentation.exception.error_rule import ErrorRuleBook
from app.presentation.exception.failure_logger import FailureLogger

FAILURE_LOGGER = "app.presentation.exception.failure_logger"


def test_스트리밍_중_실패는_로그에_error_이벤트로_응답했다고_표시한다(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    request = Request(
        {"type": "http", "method": "POST", "path": "/chat", "headers": []}
    )
    exc = UpstreamError.llm_call_failed("ConnectError")

    # When
    with caplog.at_level(logging.WARNING, logger=FAILURE_LOGGER):
        FailureLogger().log(request, ErrorRuleBook().find(exc), exc, streaming=True)

    # Then
    (record,) = [r for r in caplog.records if r.name == FAILURE_LOGGER]
    assert record.levelno == logging.ERROR
    assert "POST /chat -> 502 UPSTREAM_ERROR" in record.getMessage()
    assert "스트리밍 중: error 이벤트로 응답" in record.getMessage()
