"""스트리밍(/chat) 응답의 이벤트 틀."""

import json
from enum import StrEnum

from pydantic import BaseModel, Field

from app.api.response.error_code import ErrorCode


class SseEventName(StrEnum):
    """스트리밍 이벤트 종류. fastapi-conventions의 SSE 이벤트 표를 따른다."""

    TOKEN = "token"
    DONE = "done"
    ERROR = "error"


class SseEvent(BaseModel):
    """스트리밍 응답의 이벤트 한 개.

    생성자 대신 token(), done(), error()로 만들고 encode()로 내보낸다.
    """

    event: SseEventName = Field(description="이벤트 종류")
    data: dict[str, str] = Field(description="이벤트 내용")

    @classmethod
    def token(cls, text: str) -> "SseEvent":
        """답의 다음 조각을 담은 이벤트를 만든다."""
        return cls(event=SseEventName.TOKEN, data={"text": text})

    @classmethod
    def done(cls, conversation_id: str) -> "SseEvent":
        """답이 끝났음을 알리는 이벤트를 만든다."""
        return cls(event=SseEventName.DONE, data={"conversation_id": conversation_id})

    @classmethod
    def error(cls, code: ErrorCode, message: str) -> "SseEvent":
        """실패를 알리는 이벤트를 만든다. 이 뒤로는 아무것도 보내지 않는다.

        Args:
            code: 오류 종류. ApiResponse의 실패 응답과 같은 값을 쓴다.
            message: 사용자에게 보여줄 안내 문구.
        """
        return cls(
            event=SseEventName.ERROR, data={"code": code.value, "message": message}
        )

    def encode(self) -> str:
        """text/event-stream으로 보낼 문자열로 바꾼다.

        Returns:
            `event:` 줄, JSON 한 줄짜리 `data:` 줄, 빈 줄로 끝나는 문자열.
        """
        # 줄바꿈이 든 글자를 그대로 쓰면 이벤트가 깨져서 data는 JSON 한 줄로 쓴다.
        data = json.dumps(self.data, ensure_ascii=False)
        return f"event: {self.event.value}\ndata: {data}\n\n"
