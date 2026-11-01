from collections import deque

from litestar import Controller, get
from litestar.di import NamedDependency

from core.models.models import BoxesModel


class RootController(Controller):
    @get()
    def hello(
        self, accumulator: NamedDependency[deque[BoxesModel]]
    ) -> deque[BoxesModel]:
        return accumulator
