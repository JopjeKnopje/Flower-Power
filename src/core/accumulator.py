from collections import deque

from core.models.models import BoxesModel, Vec4f


class Accumulator:
    _data: deque[BoxesModel]

    def __init__(self) -> None:
        # HACK: Just want some atomic data without doing a refactor
        self._data = deque(maxlen=1)

    def add(self, frame_boxes: list[Vec4f] | None) -> None:
        self._data.append(BoxesModel(boxes=frame_boxes))

    def get(self) -> deque[BoxesModel]:
        return self._data
