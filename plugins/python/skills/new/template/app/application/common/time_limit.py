"""흐름 전체에 시간 제한 걸기. 채팅과 상관없는 기술이라 서비스 밖에 둔다."""

import asyncio
from collections.abc import AsyncGenerator
from typing import TypeVar

from app.common.errors import AgentTimeoutError

T = TypeVar("T")


class TimeLimit:
    """흐름 전체(첫 항목부터 마지막 항목까지)에 시간 제한을 건다."""

    def __init__(self, seconds: float) -> None:
        """시간 제한을 정한다.

        Args:
            seconds: 전체 시간 제한(초). 설계 문서 개요 "시간 제한"의 우리 쪽 값.
        """
        self._seconds = seconds

    async def apply(self, items: AsyncGenerator[T]) -> AsyncGenerator[T]:
        """items에 시간 제한을 걸어 그대로 내놓는다.

        마감 시각은 처음 한 번 정하고, 다음 항목을 기다릴 때만 그 마감으로 제한을 건다.
        내보내는 동안(yield)은 제한 밖에 둔다. yield까지 제한 안에 두면 받는 쪽이
        느릴 때 취소가 함수 밖에서 걸려 TimeoutError로 바뀌지 못한다 (PEP 789).

        Args:
            items: 시간 제한을 걸 흐름. 끝나거나 실패하면 닫는다.

        Yields:
            items가 내놓은 항목을 그대로.

        Raises:
            AgentTimeoutError: 마지막 항목까지 시간 제한을 넘겼을 때.
        """
        deadline = asyncio.get_running_loop().time() + self._seconds
        try:
            while True:
                async with asyncio.timeout_at(deadline):
                    try:
                        item = await anext(items)
                    except StopAsyncIteration:
                        return
                yield item
        except TimeoutError as e:
            raise AgentTimeoutError(
                f"에이전트 실행 시간 초과: timeout_seconds={self._seconds}"
            ) from e
        finally:
            await items.aclose()
