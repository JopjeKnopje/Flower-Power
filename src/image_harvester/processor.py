from threading import Lock
from typing import override

from cv2.typing import MatLike

from core.models.models import TestModel
from processor.processor import Processor
from processor.settings import Vec4f


class TestProcessor(Processor):
    _mutex: Lock = Lock()
    _data: TestModel

    @override
    def process(self, frame: MatLike, boxes_n: list[Vec4f]) -> None:
        with self._mutex:
            self._data = TestModel(value=len(boxes_n))

    @override
    def get_model(self) -> TestModel:
        with self._mutex:
            return self._data
