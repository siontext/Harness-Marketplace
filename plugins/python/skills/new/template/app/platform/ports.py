"""연결 창구의 모양(Protocol). 에이전트와 도구는 이 모양에만 의존한다."""

from dataclasses import dataclass
from typing import Protocol

from langchain_core.language_models import BaseChatModel


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


class LlmProvider(Protocol):
    """채팅 모델을 돌려주는 창구."""

    def chat_model(self) -> BaseChatModel:
        """에이전트가 쓸 채팅 모델을 돌려준다."""
        ...


class PromptStore(Protocol):
    """이름으로 프롬프트 문장을 가져오는 창구."""

    def get(self, name: str) -> str:
        """프롬프트 문장을 돌려준다.

        Args:
            name: 프롬프트 이름. 확장자 없이 쓴다 (예: "system").

        Raises:
            PromptNotFoundError: 그 이름의 프롬프트가 없을 때.
        """
        ...


class Guardrail(Protocol):
    """LLM 앞뒤에서 입력과 출력을 검사하는 창구."""

    async def check_input(self, text: str) -> GuardResult:
        """LLM에 보내기 전 사용자 입력을 검사한다."""
        ...

    async def check_output(self, text: str) -> GuardResult:
        """사용자에게 보내기 전 LLM 출력을 검사한다."""
        ...
