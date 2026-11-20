"""JSON으로 한 번에 답하는 엔드포인트의 공통 응답 틀 (성공·실패 공통)."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.api.response.error_code import ErrorCode

SUCCESS_CODE = "SUCCESS"

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """JSON으로 한 번에 답하는 모든 응답의 공통 틀.

    성공과 실패는 HTTP 상태 코드로 구분하므로 본문에 상태 코드를 넣지 않는다.
    생성자 대신 success()와 fail()로 만든다.
    """

    code: str = Field(description="성공이면 SUCCESS, 실패면 오류 종류")
    message: str | None = Field(
        default=None, description="실패일 때 사용자에게 보여줄 안내 문구"
    )
    data: T | None = Field(default=None, description="성공일 때 돌려줄 내용")

    @classmethod
    def success(cls, data: T | None = None) -> "ApiResponse[T]":
        """성공 응답을 만든다.

        Args:
            data: 돌려줄 내용. 없으면 None.

        Returns:
            code가 SUCCESS이고 message가 없는 응답.
        """
        return cls(code=SUCCESS_CODE, data=data)

    @classmethod
    def fail(cls, code: ErrorCode, message: str) -> "ApiResponse[T]":
        """실패 응답을 만든다.

        Args:
            code: 오류 종류.
            message: 사용자에게 보여줄 안내 문구.

        Returns:
            data가 없는 응답.
        """
        return cls(code=code.value, message=message)
