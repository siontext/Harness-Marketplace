"""요청·응답 모양. 호출하는 쪽과 주고받는 pydantic 모델을 모은다."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    """오류 응답의 code 값. fastapi-conventions 표에 있는 값만 둔다."""

    INVALID_REQUEST = "INVALID_REQUEST"
    TIMEOUT = "TIMEOUT"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    """모든 실패 응답의 본문. 칸은 code와 message 둘뿐이다."""

    code: ErrorCode = Field(description="오류 종류")
    message: str = Field(description="사용자에게 보여줄 안내 문구")
