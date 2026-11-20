"""LLM 창구의 모양. 로컬/운영 구현을 바꿔 끼우는 자리다.

에이전트 흐름(application)은 이 모양을 모른다. 답 만들기 어댑터
(app/infrastructure/agent)가 이 창구에서 채팅 모델을 받아 쓴다.
"""

from typing import Protocol

from langchain_core.language_models import BaseChatModel


class LlmProvider(Protocol):
    """채팅 모델을 돌려주는 창구."""

    def chat_model(self) -> BaseChatModel:
        """에이전트가 쓸 채팅 모델을 돌려준다."""
        ...
