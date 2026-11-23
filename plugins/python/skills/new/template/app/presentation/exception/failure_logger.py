"""실패 로그. 전역 예외 핸들러와 스트리밍 응답(SseResponse)이 같은 규칙으로 남긴다."""

import logging
from http import HTTPStatus
from typing import ClassVar

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from app.presentation.exception.error_rule import ErrorRule

logger = logging.getLogger(__name__)


class FailureLogger:
    """실패를 로그에 남긴다. 요청 본문, 쿼리 값, 헤더는 남기지 않는다."""

    _STREAMING_LOG_SUFFIX: ClassVar[str] = " [스트리밍 중: error 이벤트로 응답]"

    def log(
        self,
        request: Request,
        rule: ErrorRule,
        exc: Exception,
        *,
        streaming: bool = False,
    ) -> None:
        """실패를 남긴다. 5xx는 ERROR·스택 포함, 그 밖은 WARNING·스택 없음.

        Args:
            request: 실패한 요청.
            rule: 그 실패에 적용한 오류 규칙.
            exc: 올라온 예외.
            streaming: 스트리밍이 시작된 뒤의 실패면 True. 이때 실제 HTTP 응답은
                200이고 오류는 error 이벤트로 나가므로 로그에 그 사실을 표시한다.
        """
        suffix = self._STREAMING_LOG_SUFFIX if streaming else ""
        args = (
            request.method,
            request.url.path,
            rule.status_code,
            rule.code.value,
            type(exc).__name__,
            suffix,
        )
        if rule.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
            logger.error("서버 오류: %s %s -> %d %s (%s)%s", *args, exc_info=exc)
        else:
            logger.warning("호출자 오류: %s %s -> %d %s (%s)%s", *args)

    def log_invalid_request(
        self, request: Request, rule: ErrorRule, exc: RequestValidationError
    ) -> None:
        """요청 형식 오류를 WARNING으로 남긴다. 틀린 필드의 위치와 종류만 남긴다.

        Args:
            request: 실패한 요청.
            rule: 요청 형식 오류 규칙.
            exc: FastAPI가 던진 요청 형식 오류.
        """
        logger.warning(
            "요청 형식 오류: %s %s -> %d %s (%s) 틀린 곳: %s",
            request.method,
            request.url.path,
            rule.status_code,
            rule.code.value,
            type(exc).__name__,
            self._describe_invalid_fields(exc),
        )

    @staticmethod
    def _describe_invalid_fields(exc: RequestValidationError) -> str:
        """틀린 필드의 위치와 종류만 문장으로 만든다. 보낸 값(input)은 넣지 않는다."""
        return ", ".join(
            f"{'.'.join(str(part) for part in error['loc'])}({error['type']})"
            for error in exc.errors()
        )
