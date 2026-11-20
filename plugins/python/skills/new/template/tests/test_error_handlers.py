import logging
from http import HTTPStatus

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.common.errors import UpstreamError
from app.presentation.errors import (
    find_error_rule,
    log_failure,
    register_exception_handlers,
)
from main import app as real_app

# 예외 메시지·요청 값에 심어 두고, 응답과 로그로 새는지 확인하는 표식.
LEAK_MARKER = "leak-marker-9f3a"
HANDLER_LOGGER = "app.presentation.errors"


class _ItemRequest(BaseModel):
    count: int = Field(description="개수")


def _build_test_app() -> FastAPI:
    """핸들러를 붙이고 일부러 오류를 내는 주소를 더한 테스트용 앱."""
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"result": "ok"}

    @test_app.post("/items")
    async def create_item(item: _ItemRequest) -> dict[str, int]:
        return {"count": item.count}

    @test_app.get("/upstream-error")
    async def raise_upstream_error() -> None:
        raise UpstreamError(f"LLM 호출 실패: {LEAK_MARKER}")

    @test_app.get("/http-503")
    async def raise_http_503() -> None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail=LEAK_MARKER
        )

    @test_app.get("/http-no-body/{status_code}")
    async def raise_http_no_body(status_code: int) -> None:
        raise HTTPException(status_code=status_code, detail=LEAK_MARKER)

    @test_app.get("/unhandled")
    async def raise_unhandled() -> None:
        raise RuntimeError(f"미리 생각하지 못한 오류: {LEAK_MARKER}")

    return test_app


@pytest.fixture
def client() -> TestClient:
    # 처리하지 못한 예외는 응답 뒤에 다시 던져진다. 응답을 보려면 꺼 둔다.
    return TestClient(_build_test_app(), raise_server_exceptions=False)


def _handler_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [record for record in caplog.records if record.name == HANDLER_LOGGER]


def test_정상_응답은_핸들러가_건드리지_않는다(client: TestClient) -> None:
    # When
    response = client.get("/ok")

    # Then
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"result": "ok"}


def test_프로젝트_예외가_올라오면_대응표의_상태_코드와_본문으로_답한다(
    client: TestClient,
) -> None:
    # When
    response = client.get("/upstream-error")

    # Then
    assert response.status_code == HTTPStatus.BAD_GATEWAY
    assert response.json() == {
        "code": "UPSTREAM_ERROR",
        "message": (
            "연결된 시스템에 문제가 있어 답하지 못했습니다. 잠시 후 다시 시도해 주세요."
        ),
        "data": None,
    }


def test_요청_형식이_틀리면_422와_INVALID_REQUEST로_답한다(
    client: TestClient,
) -> None:
    # When
    response = client.post("/items", json={"count": "숫자가 아님"})

    # Then
    body = response.json()
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert body["code"] == "INVALID_REQUEST"
    assert "detail" not in body


def test_없는_주소는_404와_통일된_본문으로_답한다() -> None:
    # Given
    real_client = TestClient(real_app)

    # When
    response = real_client.get("/no-such-path")

    # Then
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "요청한 주소를 찾을 수 없습니다.",
        "data": None,
    }


def test_허용_안_된_방식은_405와_Allow_헤더를_그대로_돌려준다() -> None:
    # Given
    real_client = TestClient(real_app)

    # When
    response = real_client.post("/health")

    # Then
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response.headers["allow"] == "GET"
    assert response.json() == {
        "code": "INVALID_REQUEST",
        "message": "지원하지 않는 요청 방식입니다.",
        "data": None,
    }


def test_HTTPException_5xx는_상태_코드를_지키고_INTERNAL_ERROR로_답한다(
    client: TestClient,
) -> None:
    # When
    response = client.get("/http-503")

    # Then
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json()["code"] == "INTERNAL_ERROR"


@pytest.mark.parametrize("status", [HTTPStatus.NO_CONTENT, HTTPStatus.NOT_MODIFIED])
def test_본문을_실을_수_없는_상태_코드는_본문_없이_답한다(
    client: TestClient, status: HTTPStatus
) -> None:
    # When
    response = client.get(f"/http-no-body/{status.value}")

    # Then
    assert response.status_code == status
    assert response.content == b""


def test_처리하지_못한_예외는_500과_INTERNAL_ERROR로_답한다(
    client: TestClient,
) -> None:
    # When
    response = client.get("/unhandled")

    # Then
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json()["code"] == "INTERNAL_ERROR"


@pytest.mark.parametrize("path", ["/upstream-error", "/http-503", "/unhandled"])
def test_오류_응답에_예외_내용이_새지_않는다(client: TestClient, path: str) -> None:
    # When
    response = client.get(path)

    # Then
    assert LEAK_MARKER not in response.text
    assert set(response.json()) == {"code", "message", "data"}
    assert response.json()["data"] is None


def test_서버_오류는_ERROR_수준으로_스택과_함께_남는다(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    # When
    with caplog.at_level(logging.WARNING, logger=HANDLER_LOGGER):
        client.get("/upstream-error")

    # Then
    (record,) = _handler_records(caplog)
    assert record.levelno == logging.ERROR
    assert isinstance(record.exc_info, tuple)
    assert isinstance(record.exc_info[1], UpstreamError)


def test_호출자_오류는_WARNING_수준으로_스택_없이_남는다(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    # When
    with caplog.at_level(logging.WARNING, logger=HANDLER_LOGGER):
        client.get("/no-such-path")

    # Then
    (record,) = _handler_records(caplog)
    assert record.levelno == logging.WARNING
    assert record.exc_info is None


def test_요청_형식_오류_로그에_보낸_값이_남지_않는다(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    # When
    with caplog.at_level(logging.WARNING, logger=HANDLER_LOGGER):
        client.post(f"/items?memo={LEAK_MARKER}", json={"count": LEAK_MARKER})

    # Then
    (record,) = _handler_records(caplog)
    assert "body.count" in record.getMessage()
    assert LEAK_MARKER not in caplog.text


def test_스트리밍_중_실패는_로그에_error_이벤트로_응답했다고_표시한다(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    request = Request(
        {"type": "http", "method": "POST", "path": "/chat", "headers": []}
    )
    exc = UpstreamError("LLM 호출 실패: ConnectError")

    # When
    with caplog.at_level(logging.WARNING, logger=HANDLER_LOGGER):
        log_failure(request, find_error_rule(exc), exc, streaming=True)

    # Then
    (record,) = _handler_records(caplog)
    assert record.levelno == logging.ERROR
    assert "POST /chat -> 502 UPSTREAM_ERROR" in record.getMessage()
    assert "스트리밍 중: error 이벤트로 응답" in record.getMessage()
