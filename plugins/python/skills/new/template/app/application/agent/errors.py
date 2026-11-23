"""가드레일에 막혔을 때 채팅 서비스가 던지고 SseResponse가 이름을 적어 잡는 예외.

막힌 것은 오류가 아니라 의도된 결과라서 오류 대응표(ErrorRuleBook)에 넣지 않는다.
"""

from app.common.errors import AppError


class OutputBlockedError(AppError):
    """LLM 출력이 출력 가드레일에 막혔을 때. 오류가 아니라 의도된 결과다.

    /chat이 잡아 BLOCKED error 이벤트로 바꾸므로 오류 대응표(ErrorRuleBook)에
    넣지 않는다. 막힌 내용은 담지 않는다.

    Attributes:
        guard_message: 가드레일이 준 안내 문구. 비어 있을 수 있다.
    """

    def __init__(self, guard_message: str) -> None:
        super().__init__("출력 가드레일에 막혔다")
        self.guard_message = guard_message


class InputBlockedError(AppError):
    """질문이 입력 가드레일에 막혔을 때. 오류가 아니라 의도된 결과다.

    LLM을 부르기 전이라 SseResponse가 안내 문구를 정상 답(token → done)으로 보낸다.
    막힌 질문은 담지 않는다.

    Attributes:
        guard_message: 가드레일이 준 안내 문구. 비어 있을 수 있다.
    """

    def __init__(self, guard_message: str) -> None:
        super().__init__("입력 가드레일에 막혔다")
        self.guard_message = guard_message
