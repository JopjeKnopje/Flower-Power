from abc import ABC
from queue import LifoQueue

from cv2.typing import MatLike, Vec4f


class FrameProcessor(ABC):
    def skipped(self) -> None: ...
    def process(self, frame: MatLike, boxes_n: list[Vec4f]) -> None: ...


# TODO: Inherit
class TestProcessor:
    _data_queue: LifoQueue[int] = LifoQueue()

    def skipped(self) -> None: ...
    def process(self, frame: MatLike, boxes_n: list[Vec4f]) -> None:
        self._data_queue.put(len(boxes_n))

    @classmethod
    def get_queue(cls) -> LifoQueue[int]:
        return cls._data_queue
