from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import Literal, Protocol
import typing

import cv2
from cv2.typing import MatLike
from ultralytics import YOLO
from pathlib import Path


from image_harvester.config import Config
from image_harvester.logging import logger_init
from image_harvester.video import VideoSource, VideoStream

logger = logger_init()
# TODO: Fix this
logging.getLogger("httpx").setLevel("CRITICAL")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").propagate = False

type Vec4f = tuple[float, float, float, float]


@dataclass
class JointViewport:
    video_streams: list[VideoStream]

    def is_open(self) -> bool:
        for s in self.video_streams:
            if not s.is_open():
                return False
        return True

    def read_stream(self, id: int) -> MatLike:
        return self.video_streams[id].read()

    def read(self) -> MatLike:
        imgs: list[MatLike] = []

        for i, _ in enumerate(self.video_streams):
            img = self.read_stream(i)

            imgs.append(img)
        return cv2.hconcat(imgs)

    def release(self) -> None:
        for s in self.video_streams:
            s.release()


def recording_path_file_name(cam_id: int, part_id: int) -> str:
    return f"cam-{cam_id}-{part_id}.avi"


def recording_path_find_part_id(dir_path: Path) -> int:
    """
    Finds the closest file `part` in a file path e.g `cam-1-X`
    """

    # TODO: use some kind of class or container that keeps track of all the filepaths
    p = dir_path.glob("cam-*-*.avi")

    part_id_max = 0
    for f in p:
        if not f.is_file():
            continue

        no_suffix = f.with_suffix("").name
        part_id = int(no_suffix.split("-")[2])

        if part_id >= part_id_max:
            part_id_max = part_id + 1
    return part_id_max


class Harvester:
    # TODO: Maybe use ABC?
    class FrameProcessorType(Protocol):
        def skipped(self) -> None: ...
        def process(self, frame: MatLike, boxes_n: list[Vec4f]) -> None: ...

    def __init__(self, config: Config) -> None:
        self._config: Config = config

        self._viewport: JointViewport = JointViewport(self._init_streams(config))
        if not self._viewport.is_open():
            print("error viewport not open")
        else:
            logger.info("viewport created")

        # Load the YOLO26 model
        model_path = "yolo26n.pt"
        self._model: YOLO = YOLO(model_path)
        logger.info(f"done loading model {model_path}")

    @staticmethod
    def _recording_get_path(dir_path: Path, cam_id: int) -> Path:
        dir_path.mkdir(exist_ok=True)
        part_id = recording_path_find_part_id(dir_path)
        return dir_path.joinpath(Path(recording_path_file_name(cam_id, part_id)))

    @staticmethod
    def _init_streams(cfg: Config) -> list[VideoStream]:
        streams: list[VideoStream] = []

        for i, c in enumerate(cfg.cameras):
            writer_out_path = None
            if cfg.recording_dir:
                writer_out_path = Harvester._recording_get_path(
                    Path(f"{cfg.recording_dir}"), i
                )
            video_src = VideoSource.from_cfg_camera(c)
            stream = VideoStream(video_src, writer_out_path)
            streams.append(stream)

        logger.info(f"connected to {len(streams)} cameras")
        return streams

    def loop(
        self,
        processor: FrameProcessorType,
        headless: bool = False,
        yolo_device: Literal["cpu", "cuda"] = "cuda",
    ) -> None:

        logger.info(f"starting yolo loop on device {yolo_device}")
        while self._viewport.is_open():
            try:
                frame = self._viewport.read()
            except Exception as e:
                logger.error(e)
                continue
            # TODO: set cpu option based on cli parameter
            result = self._model.track(  # pyright: ignore[reportUnknownMemberType]
                frame,
                verbose=self._config.yolo_verbose,
                persist=False,
                # Detect only humans
                classes=[0],
                device=yolo_device,
            )[0]

            # Get the boxes and track IDs
            if result.boxes and result.boxes.is_track:
                boxes = result.boxes.xywhn.cpu().tolist()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportAttributeAccessIssue]
                boxes = typing.cast(list[Vec4f], boxes)
                processor.process(frame, boxes)
            else:
                processor.skipped()

            # Display the annotated frame
            if not headless:
                # Visualize the result on the frame
                frame = result.plot()
                height, width, _ = frame.shape  # pyright: ignore[reportAny]
                cv2.imshow(f"Flower Power @ {width}x{height}", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        self._viewport.release()
        if not headless:
            cv2.destroyAllWindows()
