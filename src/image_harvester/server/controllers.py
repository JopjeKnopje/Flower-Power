from collections import deque

from litestar import Controller, websocket_listener
from litestar.di import NamedDependency

from core.models.models import BoxesModel


class RootController(Controller):
    @websocket_listener("/")
    def hello(
        self, data: str, accumulator: NamedDependency[deque[BoxesModel]]
    ) -> deque[BoxesModel]:
        _ = data
        return accumulator
