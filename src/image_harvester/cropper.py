from typing import Any

import cv2
from cv2.typing import Point


from image_harvester.flower_config import Camera
from image_harvester.harvester import JointViewport, init_streams_from_cams
from image_harvester.logs import logger_init

logger = logger_init()


class CropSelector:
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

    def get_selected_rect(self) -> tuple[Point, Point] | None:
        # I wanna throw up
        # TODO: Use any()?
        if (
            self._point_start[0] > 0
            and self._point_start[1] > 0
            and self._point_end[0] > 0
            and self._point_end[1] > 0
        ):
            return (self._point_start, self._point_end)
        return None


class Cropper:
    def __init__(self, cams: list[Camera]) -> None:

        self._viewport: JointViewport = JointViewport(init_streams_from_cams(cams))
        if not self._viewport.is_open():
            print("error viewport not open")
        else:
            logger.info("viewport created")

    @staticmethod
    def _cycle_stream(value: int, dir: int, limit: int) -> int:
        return (value + dir) % limit

    def loop(
        self,
    ) -> None:
        current_stream_id: int = 0

        while self._viewport.is_open():
            # get a specific stream instead of the whole joined view
            current_stream = self._viewport.get_stream(current_stream_id)
            try:
                frame = current_stream.read()
            except Exception as e:
                logger.error(f"_viewport.read failed {e}")
                continue

            # height, width, _ = frame.shape  # pyright: ignore[reportAny]
            # logger.info("imshow")
            cv2.imshow("Cropping", frame)

            key_state = cv2.waitKey(1)
            if key_state & 0xFF == ord("."):
                current_stream_id = Cropper._cycle_stream(
                    current_stream_id, 1, self._viewport.stream_count
                )
                logger.error("yup")
            if key_state & 0xFF == ord(","):
                current_stream_id = Cropper._cycle_stream(
                    current_stream_id, -1, self._viewport.stream_count
                )
            if key_state & 0xFF == ord("q"):
                break

        self._viewport.release()
        cv2.destroyAllWindows()
