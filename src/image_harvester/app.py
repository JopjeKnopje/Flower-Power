from collections import deque
import platform
import sys
import pickle
from torch.cuda import is_available as cuda_is_avaliable

import cv2
from cv2.typing import MatLike
import httpx

from image_harvester.flower_api import Flower
from image_harvester.logging import logger_init
from image_harvester.config import Config
from image_harvester.harvester import Harvester, Vec4f
from image_harvester.smoothing import sma
from image_harvester.timer import Timer

logger = logger_init()


class Processor:
    _REQUEST_INTERVAL_MS: int = 2000
    _DEQUE_SIZE: int = 20

    def __init__(self, api: Flower) -> None:
        self._api: Flower = api

        self._sma_output_list: list[float] = []

        self._data_raw: list[int] = []
        self._data_raw_ringbuf: deque[float] = deque(maxlen=self._DEQUE_SIZE)
        self._timer: Timer = Timer()

    def skipped(self) -> None:
        logger.warning("skipped processing, no one detected")

    # TODO: Run async of threaded?
    def update_flower(self, pos: int) -> None:
        self._timer.start_if_not_running()
        if self._timer.delta() > self._REQUEST_INTERVAL_MS:
            # TODO: Handle connection refused when server offline
            _ = self._api.move(pos)

            self._timer.start()

    def process(self, frame: MatLike, boxes_n: list[Vec4f]) -> None:
        height, width, _ = frame.shape  # pyright: ignore[reportAny]
        value: float = 0
        for boxn in boxes_n:
            x, y, w, h = boxn
            x_pos = int((x - (w / 2)) * width)  # pyright: ignore[reportAny]
            y_pos = int(y * height)  # pyright: ignore[reportAny]

            _ = cv2.putText(
                frame,
                f"height {h:.2f}",
                (x_pos, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (20, 205, 20),
                2,
                cv2.LINE_AA,
            )
            # tracked_objects.append(int(object_height))
            value += h
        value = int((value / len(boxes_n)) * 10)
        self._data_raw_ringbuf.append(value)
        self._data_raw.append(value)
        if self._data_raw_ringbuf.maxlen is not None:
            logger.info("starting sma")
            sma_list = list(self._data_raw_ringbuf)
            sma_value = sma(sma_list, self._data_raw_ringbuf.maxlen)[-1]
            self._sma_output_list.append(sma_value)
            logger.warning(
                f"input: {self._data_raw_ringbuf[-1]} sma output: {sma_value}"
            )
            self.update_flower(int(sma_value))
        else:
            raise Exception("_points.maxlen not set, cannot perform sma")


# TODO: Make this actually something smaert
def calculate_frames(frame_h: int, obj_h: list[int]) -> int:
    close_threshold = 0.5

    close_count = 0
    away_count = 0

    for o in obj_h:
        # higher = closer
        ratio = 1 - (frame_h - o) / frame_h
        # logger.info(f"frame {ratio}")
        if ratio > close_threshold:
            close_count += 2
        else:
            away_count += 1

    value = int(close_count + away_count)
    # logger.info(f"value {value} close_count {close_count} away_count {away_count}")

    return value


def make_request(endpoint: str, value: int) -> None:
    if value >= 0 and value <= 9:
        r_str = f"{endpoint}/move?band={value}"
        r = httpx.request("GET", url=r_str)
        logger.info(f"send request {r_str}")

        log_str = f"controller HTTP: {r.status_code}"
        if r.status_code >= 400:
            logger.warning(log_str)
        elif r.status_code:
            logger.info(log_str)


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"


def main() -> None:

    # TODO: get cli args for cuda or cpu mode (also read them from config file?)

    config = Config.read()
    print(config)
    harvester = Harvester(Config.read())

    api = Flower(config.flower_endpoint)

    proc = Processor(api)

    is_headless = host_is_headless()
    yolo_device = "cuda"
    if is_headless or not cuda_is_avaliable():
        yolo_device = "cpu"

    harvester.loop(proc, yolo_device=yolo_device, headless=is_headless)

    if len(proc._data_raw) != 0:
        with open("office_people.raw", "wb") as f:
            pickle.dump(proc._data_raw, f)
    if len(proc._sma_output_list) != 0:
        with open("office_people.sma", "wb") as f:
            pickle.dump(proc._sma_output_list, f)
