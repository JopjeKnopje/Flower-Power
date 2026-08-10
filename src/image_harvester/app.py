import platform
import sys
from typing import Any

from attr import dataclass
import cv2
from cv2.typing import Point

from image_harvester.logs import logger_init

logger = logger_init()


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"


@dataclass
class CropConfig:
    _point_start: Point
    _point_end: Point
    _uri: str


class OpenCVCropper:
    # TODO: Find way of doing a fixed size list, which still supports indexing
    _point_start: Point
    _point_end: Point
    _initial_point_is_set: bool

    def __init__(self) -> None:
        self._point_start = (0, 0)
        self._point_end = (0, 0)
        self._initial_point_is_set = False

    def mouse_cb(
        self,
        event: int,
        x: int,
        y: int,
        flags: int,
        user_data: Any | None,  # pyright: ignore[reportExplicitAny]
    ) -> None:
        _ = flags
        _ = user_data

        if event == cv2.EVENT_LBUTTONDOWN and not self._initial_point_is_set:
            self._point_start = (x, y)
            self._initial_point_is_set = True

        if event == cv2.EVENT_MOUSEMOVE and self._initial_point_is_set:
            self._point_end = (x, y)

        if event == cv2.EVENT_LBUTTONUP:
            self._initial_point_is_set = False

    # _typing.Callable[[tuple[int] | tuple[int, _typing.Any]], None]
    def save_cb(self, x: tuple[int] | tuple[int, Any], user_data: Any) -> None:  # pyright: ignore[reportExplicitAny, reportAny]
        logger.info(x)
        logger.info(user_data)  # pyright: ignore[reportAny]

    def get_rect(self) -> tuple[Point, Point] | None:
        # I wanna throw up
        if (
            self._point_start[0] > 0
            and self._point_start[1] > 0
            and self._point_end[0] > 0
            and self._point_end[1] > 0
        ):
            return (self._point_start, self._point_end)
        return None
