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
    def __init__(self) -> None:
        self._process_counter: int = 0

    def skipped(self) -> None: ...

    def process(self, frame: MatLike, boxes: list[Vec4f], id: int) -> None:
        _ = id
        for box in boxes:
            h = box[3]
            _ = cv2.putText(
                frame,
                f"height {h:.2f}",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            # tracked_objects.append(int(object_height))

        logger.warning(f"called callback {self._process_counter}")
        self._process_counter += 1


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
