import platform
import sys

import cv2
from cv2.typing import MatLike
import httpx

from image_harvester.logging import logger_init
from image_harvester.config import Config
from image_harvester.harvester import Harvester, Vec4f

logger = logger_init()


class Processor:
    # this should potentially take a web-requestor to talk to the flower.
    request_interval_s: int = 5

    def __init__(self) -> None:
        self._process_count: int = 0
        self._skipped_count: int = 0

        self.value: float = 0

    def skipped(self) -> None:
        logger.warning(f"skipped {self._process_count}")
        self._skipped_count += 1

    def process(self, frame: MatLike, boxes_n: list[Vec4f]) -> None:
        self._skipped_count = 0

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
        self.value = value / len(boxes_n)

        logger.warning(f"value: {value}, self.value {self.value}")
        self._process_count += 1


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

    proc = Processor()

    is_headless = host_is_headless()
    yolo_device = "cuda"
    if is_headless:
        yolo_device = "cpu"

    harvester.loop(proc, yolo_device=yolo_device, headless=is_headless)
    # time_old = time.time() + config.flower_interval
