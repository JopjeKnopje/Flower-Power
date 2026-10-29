from queue import Empty, LifoQueue

from litestar import Controller, get
from litestar.di import NamedDependency


class RootController(Controller):
    @get()
    def hello(self, get_queue: NamedDependency[LifoQueue[int]]) -> str:

        try:
            val = get_queue.get(block=False)
        except Empty:
            val = 69

        return f"hi {val}"
