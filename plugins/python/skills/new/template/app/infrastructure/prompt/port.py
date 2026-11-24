"""프롬프트 창구의 모양. 로컬/운영 구현을 바꿔 끼우는 자리다.

에이전트 흐름(application)은 이 모양을 모른다. 조립(app/container.py)이 이 창구에서
시스템 프롬프트를 받아 답 만들기 어댑터에 넣는다.
"""

from abc import ABC, abstractmethod


class PromptStore(ABC):
    """이름으로 프롬프트 문장을 가져오는 창구."""

    @abstractmethod
    def get(self, name: str) -> str:
        """프롬프트 문장을 돌려준다.

        Args:
            name: 프롬프트 이름. 확장자 없이 쓴다 (예: "system").

        Raises:
            PromptNotFoundError: 그 이름의 프롬프트가 없을 때.
        """
        ...
