import asyncio
from collections import deque
from collections.abc import AsyncGenerator

from litestar import (
    Controller,
    get,
    websocket_stream,  # pyright: ignore[reportUnknownVariableType]
)
from litestar.di import NamedDependency

from core.accumulator import Accumulator
from core.models.models import BoxesModel


class BoxesController(Controller):
    @websocket_stream("/")
    async def stream(
        self, accumulator: NamedDependency[Accumulator]
    ) -> AsyncGenerator[BoxesModel]:
        # TODO: Only run this when new data is added to queue
        while True:
            model = accumulator.get().pop()
            yield model
            await asyncio.sleep(0.5)

    @get("/")
    async def get(self, accumulator: NamedDependency[Accumulator]) -> deque[BoxesModel]:
        return accumulator.get()
