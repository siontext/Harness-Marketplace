import asyncio

import pytest
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage

from app.application.agent.port import GuardResult
from tests.fakes import FakeGuardrail, fake_llm

# 가짜 LLM은 langchain-core 내부 동작에 기댄다. 버전이 바뀌어 깨지면 여기서 드러난다.
pytestmark = pytest.mark.anyio


def _tool_call_reply() -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": "get_item", "args": {"item_id": "A1"}, "id": "call-1"}],
    )


async def test_가짜_LLM은_스트리밍에서_도구_호출을_조각으로_낸다() -> None:
    # Given
    llm = fake_llm(_tool_call_reply())

    # When
    chunks = [chunk async for chunk in llm.astream([HumanMessage("A1 알려 줘")])]

    # Then
    merged = chunks[0]
    for chunk in chunks[1:]:
        merged += chunk
    assert isinstance(merged, AIMessageChunk)
    assert [call["name"] for call in merged.tool_calls] == ["get_item"]
    assert merged.tool_calls[0]["args"] == {"item_id": "A1"}


async def test_가짜_LLM은_받은_메시지를_차례로_기록한다() -> None:
    # Given
    llm = fake_llm(AIMessage(content="첫 답"), AIMessage(content="둘째 답"))

    # When
    await llm.ainvoke([HumanMessage("첫 질문")])
    _ = [chunk async for chunk in llm.astream([HumanMessage("둘째 질문")])]

    # Then
    assert [messages[0].content for messages in llm.received] == [
        "첫 질문",
        "둘째 질문",
    ]


async def test_가짜_가드레일은_정해_둔_시간만큼_기다렸다_결과를_준다() -> None:
    # Given
    guardrail = FakeGuardrail(
        output_results={"막힐 문장": GuardResult("", blocked=True)}, output_delay=0.05
    )
    loop = asyncio.get_running_loop()

    # When
    started = loop.time()
    result = await guardrail.check_output("막힐 문장")

    # Then
    assert loop.time() - started >= 0.05
    assert result.blocked
    assert guardrail.checked_outputs == ["막힐 문장"]
