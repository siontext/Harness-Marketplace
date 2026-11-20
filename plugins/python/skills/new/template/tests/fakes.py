"""테스트용 가짜. 바깥에 닿는 것(LLM, 연결 창구)만 가짜로 만든다."""

import json
from collections.abc import Iterator, Sequence
from itertools import chain
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.messages.tool import tool_call_chunk
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from pydantic import Field

from app.application.ports import Guardrail, GuardResult, LlmProvider, PromptStore
from app.infrastructure import Platform

FAKE_SYSTEM_PROMPT = "테스트용 시스템 프롬프트"


class FakeToolCallingModel(GenericFakeChatModel):
    """정해 둔 답을 차례로 돌려주고, 도구 연결 요청은 그대로 통과시키는 가짜 LLM.

    Attributes:
        received: 호출될 때마다 받은 메시지 목록. LLM을 불렀는지, 무엇을 받았는지 본다.
    """

    received: list[list[BaseMessage]] = Field(default_factory=list)

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "FakeToolCallingModel":
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.received.append(list(messages))
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        # 부모는 스트리밍에서 도구 호출을 조각에 싣지 않는다. 내용이 빈 도구 호출
        # 답은 조각이 하나도 나오지 않아 오류가 난다. 그래서 직접 조각으로 낸다.
        reply = next(self.messages)
        if isinstance(reply, AIMessage) and reply.tool_calls:
            self.received.append(list(messages))
            yield ChatGenerationChunk(message=_to_tool_call_chunk(reply))
            return
        self.messages = chain([reply], self.messages)
        yield from super()._stream(
            messages, stop=stop, run_manager=run_manager, **kwargs
        )


class FakeLlmProvider(LlmProvider):
    """정해 둔 채팅 모델을 돌려주는 가짜 LLM 창구."""

    def __init__(self, model: BaseChatModel) -> None:
        self._model = model

    def chat_model(self) -> BaseChatModel:
        return self._model


class FakePromptStore(PromptStore):
    """어떤 이름이든 같은 문장을 돌려주는 가짜 프롬프트 창구."""

    def get(self, name: str) -> str:
        return FAKE_SYSTEM_PROMPT


class FakeGuardrail(Guardrail):
    """그대로 통과시키되, 정해 둔 문장만 다른 검사 결과로 바꿔 돌려주는 가짜 가드레일.

    Attributes:
        checked_inputs: 입력 검사에 들어온 문장들.
        checked_outputs: 출력 검사에 들어온 문장들.
    """

    def __init__(
        self,
        input_results: dict[str, GuardResult] | None = None,
        output_results: dict[str, GuardResult] | None = None,
    ) -> None:
        self._input_results = input_results or {}
        self._output_results = output_results or {}
        self.checked_inputs: list[str] = []
        self.checked_outputs: list[str] = []

    async def check_input(self, text: str) -> GuardResult:
        self.checked_inputs.append(text)
        return self._input_results.get(text, GuardResult(text=text))

    async def check_output(self, text: str) -> GuardResult:
        self.checked_outputs.append(text)
        return self._output_results.get(text, GuardResult(text=text))


def fake_llm(*replies: AIMessage | Exception) -> FakeToolCallingModel:
    """replies를 차례로 돌려주는 가짜 LLM을 만든다.

    Args:
        replies: 차례로 돌려줄 답. 예외를 넣으면 그 차례의 LLM 호출이 실패한다.
    """
    return FakeToolCallingModel(messages=_iterate_replies(replies))


def fake_platform(llm: BaseChatModel, guardrail: Guardrail | None = None) -> Platform:
    """가짜 창구로 연결 창구 묶음을 만든다. 조립은 진짜 조립 함수에 맡긴다.

    창구가 늘면(저장소 등) 인자를 더해 가짜를 넣는다.

    Args:
        llm: 가짜 LLM.
        guardrail: 가짜 가드레일. 없으면 그대로 통과시킨다.
    """
    return Platform(
        llm=FakeLlmProvider(llm),
        prompts=FakePromptStore(),
        guardrail=guardrail or FakeGuardrail(),
    )


def _iterate_replies(replies: Sequence[AIMessage | Exception]) -> Iterator[AIMessage]:
    """답을 차례로 내고, 예외 차례가 오면 그 예외를 던진다."""
    for reply in replies:
        if isinstance(reply, Exception):
            raise reply
        yield reply


def _to_tool_call_chunk(reply: AIMessage) -> AIMessageChunk:
    """도구 호출 답을 도구 호출이 실린 스트리밍 조각 하나로 바꾼다."""
    return AIMessageChunk(
        content=reply.content,
        id=reply.id,
        tool_call_chunks=[
            tool_call_chunk(
                name=call["name"],
                args=json.dumps(call["args"], ensure_ascii=False),
                id=call["id"],
                index=index,
            )
            for index, call in enumerate(reply.tool_calls)
        ],
    )
