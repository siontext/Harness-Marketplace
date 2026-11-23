"""흐름 전체 시간 제한 테스트."""

import asyncio
from collections.abc import AsyncGenerator

import pytest

from app.application.common.time_limit import TimeLimit
from app.common.errors import AgentTimeoutError

pytestmark = pytest.mark.anyio


class _Items:
    """항목마다 정해 둔 시간만큼 기다렸다 내놓고, 닫혔는지 기록하는 흐름."""

    def __init__(self, *items: str, delay: float = 0) -> None:
        self._items = items
        self._delay = delay
        self.closed = False

    async def stream(self) -> AsyncGenerator[str]:
        try:
            for item in self._items:
                await asyncio.sleep(self._delay)
                yield item
        finally:
            self.closed = True


async def test_제한_안에_끝나면_항목을_그대로_내놓고_흐름을_닫는다() -> None:
    # Given
    items = _Items("가", "나", "다")

    # When
    result = [item async for item in TimeLimit(1).apply(items.stream())]

    # Then
    assert result == ["가", "나", "다"]
    assert items.closed


async def test_항목마다_기다린_시간이_짧아도_전체_시간을_넘으면_시간_초과다() -> None:
    # Given: 항목 하나는 0.05초라 제한(0.12초)보다 짧지만 5개를 합치면 넘는다.
    items = _Items("가", "나", "다", "라", "마", delay=0.05)
    received: list[str] = []

    # When / Then
    with pytest.raises(AgentTimeoutError):
        async for item in TimeLimit(0.12).apply(items.stream()):
            received.append(item)
    assert 0 < len(received) < 5
    assert items.closed


async def test_받는_쪽이_느려도_시간_초과는_AgentTimeoutError로_바뀐다() -> None:
    # Given: yield를 제한 안에 두면 이때 취소가 밖에서 걸려 예외가 바뀌지 못한다.
    items = _Items("가", "나")

    # When / Then
    with pytest.raises(AgentTimeoutError):
        async for _item in TimeLimit(0.05).apply(items.stream()):
            await asyncio.sleep(0.1)
