from enum import StrEnum
from pathlib import Path
from typing import Any, override

import cv2
from cv2.typing import MatLike, Point


from image_harvester.flower_config import Camera
from image_harvester.harvester import CropSettings, JointViewport, init_streams_from_cams
from image_harvester.logs import logger_init
from image_harvester.settings import Settings

logger = logger_init()




# gnarly
class CropSelector:
    _crop_settings: CropSettings
    _p1: Point
    _p2: Point
    _initial_point_is_set: bool

    def __init__(self) -> None:
        self._crop_settings = CropSettings()
        self._p1 = (0, 0)
        self._p2 = (0, 0)
        self._initial_point_is_set = False

    @property
    def settings(self) -> CropSettings:
        return self._crop_settings

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
            self._p1 = (x, y)
            self._initial_point_is_set = True

        if event == cv2.EVENT_MOUSEMOVE and self._initial_point_is_set:
            self._p2 = (x, y)

        if event == cv2.EVENT_LBUTTONUP:
            self._initial_point_is_set = False
            self._sort_settings(start=self._p1, end=self._p2)

    def _sort_settings(self, start: Point, end: Point) -> None: # ensure that start is always smaller than end
        if start[0] > self._crop_settings.start_x and start[1] > self._crop_settings.end_x:
            tmp = self._crop_settings.end_x
            self._crop_settings.end_x = start[0]
            self._crop_settings.start_x = tmp
        else:
            self._crop_settings.start_x = start[0]
        if start[1] > self._crop_settings.start_y and start[1] > self._crop_settings.end_y:
            tmp = self._crop_settings.end_y
            self._crop_settings.end_y = start[1]
            self._crop_settings.start_y = tmp
        else:
            self._crop_settings.start_y = start[1]

        if end[0] < self._crop_settings.start_x and end[0] < self._crop_settings.end_x:
            tmp = self._crop_settings.start_x
            self._crop_settings.start_x = end[0]
            self._crop_settings.end_x = tmp
        else:
            self._crop_settings.end_x = end[0]

        if end[1] < self._crop_settings.start_y and end[0] < self._crop_settings.end_y:
            tmp = self._crop_settings.start_y
            self._crop_settings.start_y = end[1]
            self._crop_settings.end_y = tmp
        else:
            self._crop_settings.end_y = end[1]

    # TODO: figure out why the selection gets too large when retuning a `Rect`
    def get_selected_rect(self) -> tuple[Point, Point] | None:
        # I wanna throw up
        # TODO: Use any()?
        if (
            self._p1[0] < 0
            or self._p1[0] < 0
            or self._p2[0] < 0
            or self._p2[1] < 0
        ):
            return None
        return (self._p1, self._p2)

    @override
    def __repr__(self) -> str:
        return f"crop_start{self._crop_settings.start}, crop_end{self._crop_settings.end}"


class Cropper:
    _viewport: JointViewport
    _crops: list[CropSelector] = []

    class Config(StrEnum):
        WINDOW_NAME = "Flower Power - Cropping"

    def __init__(self, cams: list[Camera]) -> None:

        self._viewport = JointViewport(init_streams_from_cams(cams))
        # TODO: Put this checking code in JointViewport itself.
        if not self._viewport.is_open():
            print("error viewport not open")
        else:
            logger.info("viewport created")

        self._crops = [CropSelector() for _ in range(self._viewport.stream_count)]

    # TODO: call this update stream or something like that
    def _cycle_stream(self, value: int, dir: int, limit: int) -> int:
        cur_stream_id = (value + dir) % limit
        cv2.setMouseCallback(
            self.Config.WINDOW_NAME, self._crops[cur_stream_id].mouse_cb
        )
        return cur_stream_id

    @staticmethod
    def save(file_name: Path, settings: CropSettings) -> None:
        """
        Save current CropSelector to JSON file, it will overwrite the file if it already exists.
        """

        path = Settings.CROP_SAVE_DIR.joinpath(file_name)
        path.parents[0].mkdir(exist_ok=True)
        _ = path.write_bytes(settings.encode())
        logger.info(f"wrote crop settings to file {path.as_posix()} {settings}")

    @staticmethod
    def _put_text(frame: MatLike, text: str, p: Point, font_size: float = 1.0) -> None:
        _ = cv2.putText(
            frame,
            text,
            p,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_size,
            (0, 0, 200),
            2,
            cv2.LINE_AA,
        )

    def loop(
        self,
    ) -> None:
        stream_id: int = 0

        cv2.namedWindow(self.Config.WINDOW_NAME)
        cv2.setMouseCallback(self.Config.WINDOW_NAME, self._crops[0].mouse_cb)
        while self._viewport.is_open():
            # get a specific stream rather than the whole joined-view
            current_stream = self._viewport.get_stream(stream_id)
            crop_selector = self._crops[stream_id]
            try:
                frame = current_stream.read()
            except Exception as e:
                logger.error(f"_viewport.read failed {e}")
                continue

            rect = crop_selector.get_selected_rect()
            if rect:
                _ = cv2.rectangle(frame, rect[0], rect[1], 0, 2)
                width = abs(rect[0][0] - rect[1][0])
                height = abs(rect[0][1] - rect[1][1])
                self._put_text(frame, f"w: {width}", (0, 70), 1.0)
                self._put_text(frame, f"h: {height}", (0, 105), 1.0)

            self._put_text(frame, current_stream.get_identifier(), (0, 30))

            cv2.imshow(self.Config.WINDOW_NAME, frame)
            key_state = cv2.waitKey(1)
            if key_state & 0xFF == ord("."):
                stream_id = self._cycle_stream(
                    stream_id, 1, self._viewport.stream_count
                )
            if key_state & 0xFF == ord(","):
                stream_id = self._cycle_stream(
                    stream_id, -1, self._viewport.stream_count
                )
            if key_state & 0xFF == ord("s"):
                self.save(Path(current_stream.get_identifier()), crop_selector.settings)
            if key_state & 0xFF == ord("q"):
                break

        self._viewport.release()
        cv2.destroyAllWindows()
