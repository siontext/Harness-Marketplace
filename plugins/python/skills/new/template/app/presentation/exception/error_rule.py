"""오류 규칙과 예외 → 규칙 대응표.

예외 → 상태 코드·code·안내 문구 대응은 ErrorRuleBook의 표 한 곳에만 둔다.
안내 문구 자체는 app/presentation/response/messages.py에 모아 둔다.
전역 예외 핸들러와 스트리밍 응답(SseResponse)이 같은 표를 쓴다.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from http import HTTPStatus
from typing import ClassVar

from fastapi.responses import JSONResponse, Response

from app.common.errors import AgentTimeoutError, AppError, UpstreamError
from app.presentation.response import messages
from app.presentation.response.api_response import ApiResponse
from app.presentation.response.error_code import ErrorCode


@dataclass(frozen=True)
class ErrorRule:
    """오류 하나를 무엇으로 답할지 정한 규칙.

    Attributes:
        status_code: HTTP 상태 코드.
        code: 오류 응답의 code 값.
        message: 사용자에게 보여줄 고정 안내 문구.
    """

    # 본문을 실을 수 없는 상태 코드.
    _NO_BODY_STATUS_CODES: ClassVar[frozenset[int]] = frozenset(
        {HTTPStatus.NO_CONTENT, HTTPStatus.RESET_CONTENT, HTTPStatus.NOT_MODIFIED}
    )

    status_code: int
    code: ErrorCode
    message: str

    def to_response(self, headers: Mapping[str, str] | None = None) -> Response:
        """이 규칙을 오류 응답으로 바꾼다. 본문을 실을 수 없는 상태 코드는 본문을 뺀다.

        Args:
            headers: 응답에 그대로 실을 헤더 (예: 405의 Allow).

        Returns:
            ApiResponse 실패 본문을 실은 응답. 본문을 실을 수 없으면 상태 코드만.
        """
        status_code = self.status_code
        if status_code < HTTPStatus.OK or status_code in self._NO_BODY_STATUS_CODES:
            return Response(status_code=status_code, headers=headers)
        body = ApiResponse[None].fail(self.code, self.message)
        return JSONResponse(
            body.model_dump(mode="json"), status_code=status_code, headers=headers
        )


class ErrorRuleBook:
    """올라온 예외를 무엇으로 답할지 정한 대응표.

    표는 이 클래스만 갖고, 밖에서는 find 메서드로 묻는다. 전역 핸들러와
    스트리밍 응답(SseResponse)이 같은 표를 쓰도록 이 클래스를 거친다.
    """

    # ── 예상하지 못한 오류 (기본값) ─────────────────────────────────────
    # 아래 어디에도 해당하지 않는 오류는 모두 이 규칙으로 답한다.
    _INTERNAL_ERROR_RULE: ClassVar[ErrorRule] = ErrorRule(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        ErrorCode.INTERNAL_ERROR,
        messages.INTERNAL_ERROR,
    )

    # ── 우리가 만든 예외 (app/common/errors.py) ────────────────────────────
    # 예외 → 상태 코드·code·안내 문구 대응은 이 표 한 곳에만 둔다.
    _ERROR_RULES: ClassVar[Mapping[type[AppError], ErrorRule]] = {
        AgentTimeoutError: ErrorRule(
            HTTPStatus.GATEWAY_TIMEOUT,
            ErrorCode.TIMEOUT,
            messages.TIMEOUT,
        ),
        UpstreamError: ErrorRule(
            HTTPStatus.BAD_GATEWAY,
            ErrorCode.UPSTREAM_ERROR,
            messages.UPSTREAM_ERROR,
        ),
        AppError: _INTERNAL_ERROR_RULE,
    }

    # ── FastAPI가 던지는 예외 ───────────────────────────────────────────
    # 요청 형식 오류(RequestValidationError).
    _INVALID_REQUEST_RULE: ClassVar[ErrorRule] = ErrorRule(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        ErrorCode.INVALID_REQUEST,
        messages.INVALID_REQUEST,
    )

    # HTTPException은 상태 코드를 그대로 쓰므로 4xx의 안내 문구만 상태 코드로 고른다.
    _HTTP_CLIENT_ERROR_MESSAGES: ClassVar[Mapping[int, str]] = {
        HTTPStatus.NOT_FOUND: messages.NOT_FOUND,
        HTTPStatus.METHOD_NOT_ALLOWED: messages.METHOD_NOT_ALLOWED,
    }

    def find(self, exc: Exception) -> ErrorRule:
        """예외에 맞는 오류 규칙을 찾는다.

        대응표에 없는 하위 예외는 상속을 따라 가장 가까운 부모의 규칙을 쓴다.

        Args:
            exc: 올라온 예외.

        Returns:
            그 예외의 규칙. 프로젝트 예외가 아니면 500 · INTERNAL_ERROR 규칙.
        """
        for exc_type in type(exc).__mro__:
            rule = self._ERROR_RULES.get(exc_type)
            if rule is not None:
                return rule
        return self._INTERNAL_ERROR_RULE

    def find_for_status(self, status_code: int) -> ErrorRule:
        """HTTPException의 상태 코드는 그대로 두고 code와 안내 문구를 고른다.

        Args:
            status_code: HTTPException의 상태 코드.

        Returns:
            5xx면 그 상태 코드의 INTERNAL_ERROR 규칙, 4xx면 INVALID_REQUEST 규칙.
        """
        if status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            return replace(self._INTERNAL_ERROR_RULE, status_code=status_code)
        message = self._HTTP_CLIENT_ERROR_MESSAGES.get(
            status_code, messages.CLIENT_ERROR
        )
        return ErrorRule(status_code, ErrorCode.INVALID_REQUEST, message)

    def find_for_invalid_request(self) -> ErrorRule:
        """요청 형식 오류(RequestValidationError)의 규칙을 돌려준다.

        Returns:
            422 · INVALID_REQUEST 규칙.
        """
        return self._INVALID_REQUEST_RULE

    def find_for_unexpected(self) -> ErrorRule:
        """처리하지 못한 예외의 규칙을 돌려준다.

        Returns:
            500 · INTERNAL_ERROR 규칙.
        """
        return self._INTERNAL_ERROR_RULE
