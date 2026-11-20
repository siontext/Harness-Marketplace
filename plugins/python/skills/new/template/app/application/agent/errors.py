"""에이전트 흐름 안에서 던지고 /chat이 이름을 적어 잡는 예외."""

from app.errors import AppError


class OutputBlockedError(AppError):
    """LLM 출력이 출력 가드레일에 막혔을 때. 오류가 아니라 의도된 결과다.

    /chat이 잡아 BLOCKED error 이벤트로 바꾸므로 오류 대응표(ERROR_RULES)에
    넣지 않는다. 막힌 내용은 담지 않는다.

    Attributes:
        guard_message: 가드레일이 준 안내 문구. 비어 있을 수 있다.
    """

    def __init__(self, guard_message: str) -> None:
        super().__init__("출력 가드레일에 막혔다")
        self.guard_message = guard_message
