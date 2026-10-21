"""테스트용 가짜. 바깥에 닿는 것(LLM, 연결 창구)만 가짜로 만든다."""

from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage


class FakeToolCallingModel(GenericFakeChatModel):
    """정해 둔 답을 차례로 돌려주고, 도구 연결 요청은 그대로 통과시키는 가짜 LLM."""

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "FakeToolCallingModel":
        return self


def fake_llm(*replies: AIMessage) -> FakeToolCallingModel:
    """replies를 차례로 돌려주는 가짜 LLM을 만든다."""
    return FakeToolCallingModel(messages=iter(replies))
