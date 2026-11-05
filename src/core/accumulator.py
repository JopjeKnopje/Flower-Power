from collections import deque

from core.models.models import BoxesModel, Vec4f


class Accumulator:
    _data: deque[BoxesModel]

    def __init__(self) -> None:
        self._data = deque(maxlen=16)

    def add(self, frame_boxes: list[Vec4f] | None) -> None:
        self._data.append(BoxesModel(box=frame_boxes))

    def get(self) -> deque[BoxesModel]:
        return self._data
