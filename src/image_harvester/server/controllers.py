import asyncio
from collections import deque
from collections.abc import AsyncGenerator

from litestar import (
    Controller,
    websocket_stream,  # pyright: ignore[reportUnknownVariableType]
)
from litestar.di import NamedDependency

from core.models.models import BoxesModel


class RootController(Controller):
    @websocket_stream("/")
    async def hello(
        self, accumulator: NamedDependency[deque[BoxesModel]]
    ) -> AsyncGenerator[BoxesModel]:
        # TODO: Only run this when new data is added to queue
        while True:
            model = accumulator.pop()
            yield model
            await asyncio.sleep(0.5)
