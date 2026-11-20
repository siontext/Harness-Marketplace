"""답 만들기 어댑터 테스트. 가짜 LLM과 작은 도구로 LangGraph 번역을 확인한다."""

import pytest
from langchain.tools import tool
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from app.common.errors import UpstreamError
from app.infrastructure.agent.langgraph_answer_generator import (
    LangGraphAnswerGenerator,
)
from tests.fakes import FakeToolCallingModel, fake_llm

pytestmark = pytest.mark.anyio

SYSTEM_PROMPT = "테스트용 시스템 프롬프트"


@tool(parse_docstring=True)
def get_item(item_id: str) -> str:
    """상품 번호로 상품 이름을 알려 준다.

    Args:
        item_id: 상품 번호.
    """
    return f"상품 {item_id}: 커피"


@tool(parse_docstring=True)
def broken_tool(item_id: str) -> str:
    """코드 버그가 있는 도구.

    Args:
        item_id: 상품 번호.
    """
    raise RuntimeError("도구 코드 버그")


def _tool_call(name: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": {"item_id": "A1"}, "id": "call-1"}],
    )


async def _ask(llm: FakeToolCallingModel, question: str = "A1 알려 줘") -> str:
    answers = LangGraphAnswerGenerator(
        model=llm, tools=[get_item, broken_tool], system_prompt=SYSTEM_PROMPT
    )
    return "".join([text async for text in answers.stream(question)])


@pytest.mark.parametrize(
    "streaming", [True, False], ids=["조각으로_답함", "한_번에_답함"]
)
async def test_LLM이_조각으로_보내든_한_번에_보내든_같은_답_글자를_내놓는다(
    streaming: bool,
) -> None:
    # Given: 조각 보내기를 지원하지 않는 LLM이어도 답이 비지 않아야 한다.
    llm = fake_llm(
        _tool_call("get_item"),
        AIMessage(content="A1은 커피입니다. 더 궁금한 게 있나요?"),
        streaming=streaming,
    )

    # When
    answer = await _ask(llm)

    # Then: 도구 호출과 도구 결과는 섞이지 않는다.
    assert answer == "A1은 커피입니다. 더 궁금한 게 있나요?"


async def test_시스템_프롬프트와_질문이_LLM에_가고_도구_결과가_다음_호출에_간다() -> (
    None
):
    # Given
    llm = fake_llm(_tool_call("get_item"), AIMessage(content="커피입니다."))

    # When
    await _ask(llm, "A1이 뭐야?")

    # Then
    system, question = llm.received[0]
    assert isinstance(system, SystemMessage)
    assert system.text == SYSTEM_PROMPT
    assert question.text == "A1이 뭐야?"
    tool_results = [m.text for m in llm.received[1] if isinstance(m, ToolMessage)]
    assert tool_results == ["상품 A1: 커피"]


async def test_LLM_호출이_실패하면_UpstreamError로_바뀐다() -> None:
    # Given
    llm = fake_llm(ConnectionError("LLM 서버에 닿지 않음"))

    # When / Then
    with pytest.raises(UpstreamError) as caught:
        await _ask(llm)
    assert isinstance(caught.value.__cause__, ConnectionError)


async def test_도구의_코드_버그는_UpstreamError로_바뀌지_않는다() -> None:
    # Given
    llm = fake_llm(_tool_call("broken_tool"))

    # When / Then
    with pytest.raises(RuntimeError, match="도구 코드 버그"):
        await _ask(llm)
