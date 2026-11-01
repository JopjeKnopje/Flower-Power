import statistics
from abc import ABC
from collections import deque
from typing import override

import httpx

# TODO: Use timeit timer instead?
from core.flower_api import FlowerAPI
from core.logs import logger_init
from core.models.models import Vec4f
from core.smoothing import sma
from processor.timer import Timer

logger = logger_init()


class Processor(ABC):
    # TODO: All of the derrived classes will be static.
    def skipped(self) -> None: ...
    # TODO: get called as fast as possible, it should prob take a delta time.
    def process(self, boxes: list[Vec4f]) -> None: ...  # pyright: ignore[reportUnusedParameter]


class CloseProcessor(Processor):
    _REQUEST_INTERVAL_MS: int = 1000
    _DEQUE_SIZE: int = 1

    def __init__(self, api: FlowerAPI) -> None:
        self._api: FlowerAPI = api

        self._sma_output_list: list[float] = []

        self._data_raw: list[int] = []
        self._data_raw_ringbuf: deque[float] = deque(maxlen=self._DEQUE_SIZE)
        self._timer: Timer = Timer()

    # TODO: Run async of threaded?
    def update_flower(self, pos: int) -> None:
        self._timer.start_if_not_running()
        if self._timer.delta() > self._REQUEST_INTERVAL_MS:
            try:
                _ = self._api.move(pos)
            except httpx.ConnectError as e:
                logger.exception(e)

            self._timer.start()

    @override
    def process(self, boxes: list[Vec4f]) -> None:
        # TODO: Fix this formula for new format
        value: float = 0
        # height, width = 1000, 1000
        # for boxn in boxes:
        #     x, y, w, h = boxn
        #     x_pos = int((x - (w / 2)) * width)
        #     y_pos = int(y * height)
        #
        #     _ = cv2.putText(
        #         frame,
        #         f"height {h:.2f}",
        #         (x_pos, y_pos),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         1.0,
        #         (20, 205, 20),
        #         2,
        #         cv2.LINE_AA,
        #     )
        #     tracked_objects.append(int(object_height))
        #     value += h
        value = int((value / len(boxes)) * 10)
        self._data_raw_ringbuf.append(value + 0.5)
        self._data_raw.append(value)
        if self._data_raw_ringbuf.maxlen is not None:
            # logger.info("starting sma")
            sma_list = list(self._data_raw_ringbuf)
            sma_value = sma(sma_list, self._data_raw_ringbuf.maxlen)[-1]
            self._sma_output_list.append(sma_value)
            logger.warning(
                f"input: {self._data_raw_ringbuf[-1]} sma output: {sma_value}"
            )
            self.update_flower(int(sma_value))
        else:
            raise Exception("_points.maxlen not set, cannot perform sma")


class PeopleCounter(Processor):
    _REQUEST_INTERVAL_MS: int = 5000
    _DEQUE_SIZE: int = 3

    def __init__(self, api: FlowerAPI) -> None:
        self._old_values: deque[int] = deque(maxlen=self._DEQUE_SIZE)
        self._api: FlowerAPI = api
        self._timer: Timer = Timer()

    def _get_average(self) -> int | None:
        lst = list(self._old_values)
        if len(lst) > 0:
            logger.info("")
            return int(statistics.mean(lst) + 0.5)
        return None

    # TODO: Run async of threaded?
    def update_flower(self, pos: int) -> None:

        self._timer.start_if_not_running()
        avg_val = self._get_average()

        logger.info(f"added new value to sample list {pos}")

        if self._timer.delta() > self._REQUEST_INTERVAL_MS:
            try:
                if avg_val is not None:
                    logger.info(f"sending people count {avg_val}")
                    _ = self._api.people(avg_val)
            except httpx.ConnectError as e:
                logger.exception(e)

            self._old_values.append(pos)
            self._timer.start()

    @override
    def process(self, boxes: list[Vec4f]) -> None:
        # TODO: Maybe we do some smoothing here?
        # just pass the info along to the flower
        self.update_flower(len(boxes))
