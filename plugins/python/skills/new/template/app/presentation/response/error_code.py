"""오류 응답의 code 값."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """오류 응답의 code 값. fastapi-conventions 표에 있는 값만 둔다."""

    INVALID_REQUEST = "INVALID_REQUEST"
    TIMEOUT = "TIMEOUT"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BLOCKED = "BLOCKED"
