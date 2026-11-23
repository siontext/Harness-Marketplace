"""글자 조각 흐름 → 문장 흐름 테스트."""

from collections.abc import AsyncIterator

import pytest

from app.application.common.sentences import SentenceSplitter

pytestmark = pytest.mark.anyio


async def _chunks(*texts: str) -> AsyncIterator[str]:
    for text in texts:
        yield text


async def _sentences(*texts: str) -> list[str]:
    return [sentence async for sentence in SentenceSplitter().split(_chunks(*texts))]


async def test_조각이_나뉘어_와도_문장이_끝날_때마다_내보낸다() -> None:
    # When
    sentences = await _sentences("주문은 배", "송 중입니다. 다른", " 문의가 있나요?")

    # Then
    assert sentences == ["주문은 배송 중입니다. ", "다른 문의가 있나요?"]


async def test_공백·줄바꿈에서_끊고_숫자_뒤_점과_공백_없는_점에서는_안_끊는다() -> None:
    # When
    sentences = await _sentences(
        "방법은 두 가지입니다.\n1. 번호를 확인합니다.\n3.5일 걸립니다! 끝"
    )

    # Then
    assert sentences == [
        "방법은 두 가지입니다.\n",
        "1. 번호를 확인합니다.\n",
        "3.5일 걸립니다! ",
        "끝",
    ]


async def test_이어_붙이면_원래_글자가_된다() -> None:
    # Given
    texts = ("첫 문장. 둘", "째 문장?\n셋째", " 문장")

    # When
    sentences = await _sentences(*texts)

    # Then
    assert "".join(sentences) == "".join(texts)


async def test_글자가_없으면_아무것도_내보내지_않는다() -> None:
    # When / Then
    assert await _sentences() == []
