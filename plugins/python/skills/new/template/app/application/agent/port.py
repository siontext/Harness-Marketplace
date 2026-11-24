"""에이전트 흐름이 바깥에 요구하는 모양(나가는 포트): 답 만들기, 가드레일.

LangChain 같은 프레임워크의 모양은 여기에 드러내지 않는다. 답은 글자로만 주고받는다.
구현(어댑터)은 app/infrastructure에 두고 app/container.py가 골라 넣어 준다.
업무 기능의 포트는 그 기능 폴더(app/application/<기능>/port.py)에 둔다.
포트는 ABC이고 모든 메서드에 @abstractmethod를 붙인다. 본문은 넣지 않는다.
구현 클래스는 포트를 괄호에 적어 상속한다.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardResult:
    """가드레일 검사 결과.

    Attributes:
        text: 검사를 거친 문장. 개인정보 등이 가려졌을 수 있다.
        blocked: 막혔으면 True.
        message: 막혔을 때 사용자에게 보여줄 안내 문구.
    """

    text: str
    blocked: bool = False
    message: str = ""


class Guardrail(ABC):
    """LLM 앞뒤에서 입력과 출력을 검사하는 창구."""

    @abstractmethod
    async def check_input(self, text: str) -> GuardResult:
        """LLM에 보내기 전 사용자 입력을 검사한다."""
        ...

    @abstractmethod
    async def check_output(self, text: str) -> GuardResult:
        """사용자에게 보내기 전 LLM 출력을 검사한다."""
        ...


class AnswerGenerator(ABC):
    """질문을 받아 답 글자를 조각으로 내놓는 창구. LLM과 도구 실행은 이 뒤에 있다."""

    @abstractmethod
    def stream(self, question: str) -> AsyncIterator[str]:
        """질문에 대한 답 글자를 만들어지는 대로 내놓는다.

        LLM이 답을 조각으로 보내든 한 번에 보내든 같은 모양(글자 조각)으로 내놓는다.
        도구 호출과 도구 결과는 내놓지 않는다. 이어 붙이면 답 전체가 된다.

        Args:
            question: 입력 검사를 거친 질문.

        Raises:
            UpstreamError: LLM 호출이 실패했을 때.
        """
        ...
