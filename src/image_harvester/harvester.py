from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Protocol, Self
import typing

from image_harvester.settings import Settings
from cv2.typing import MatLike, Point
import cv2
import msgspec
from ultralytics import YOLO
from pathlib import Path


from image_harvester.flower_config import Camera, FlowerConfig
from image_harvester.logs import logger_init
from image_harvester.video import VideoSource, VideoStream

logger = logger_init()

type Vec4f = tuple[float, float, float, float]


@dataclass
class CropSettings:
    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0

    @classmethod
    def load_all(cls) -> list[Self]:

        lst: list[Self] = []

        # match all files which are IPV4 address, later we should implement this cropping for a buncha diff video feeds too
        path = Path(Settings.CROP_SAVE_DIR).glob("*.*.*.*")
        for f in path:
            data = cls.decode(f.read_bytes())
            logger.info(f"loaded crop file {f} with data {data}")
            lst.append(data)
        logger.info(lst)
        return lst

    @classmethod
    def decode(cls, data: bytes) -> Self:
        return msgspec.json.decode(data, type=cls)

    def encode(self) -> bytes:
        return msgspec.json.encode(self)

    @property
    def start(self) -> Point:
        return (self.start_x, self.start_y)

    @property
    def end(self) -> Point:
        return (self.end_x, self.end_y)


@dataclass
class JointViewport:
    _video_streams: list[VideoStream]
    _crop_settings: list[CropSettings] | None = None
    _crop_max_width: int = 0

    def __post_init__(self):
        if self._crop_settings:
            self._crop_max_width = self._find_largest_crop()

    def is_open(self) -> bool:
        for s in self._video_streams:
            if not s.is_open():
                return False
        return True

    def get_stream(self, id: int = 0) -> VideoStream:
        return self._video_streams[id]

    def read_stream(self, id: int) -> MatLike:
        return self.get_stream(id).read()

    def _find_largest_crop(self) -> int:
        max_width = 0
        if not self._crop_settings:
            return max_width

        for c in self._crop_settings:
            h = c.end_x - c.start_x
            if h > max_width:
                max_width = h
        return max_width

    # TODO: Find best fitting resize for algo
    def read(self) -> MatLike:
        imgs: list[MatLike] = []

        for i, _ in enumerate(self._video_streams):
            img = self.read_stream(i)
            if self._crop_settings:
                crop = self._crop_settings[i]
                _, original_width, _ = img.shape  # pyright: ignore[reportAny]

                if original_width > self._crop_max_width:
                    img = img[crop.start_y : crop.end_y, crop.start_x : crop.end_x]
                    cropped_height = crop.end_y - crop.start_y
                    img = cv2.resize(img, (self._crop_max_width, cropped_height))
            imgs.append(img)
        return cv2.vconcat(imgs)

    @property
    def stream_count(self) -> int:
        return len(self._video_streams)

    def release(self) -> None:
        for s in self._video_streams:
            s.release()


def init_streams_from_cams(
    cams: list[Camera], recording_dir: str | None = None
) -> list[VideoStream]:
    streams: list[VideoStream] = []

    for i, c in enumerate(cams):
        writer_out_path = None
        if recording_dir:
            writer_out_path = recording_get_path(Path(recording_dir), i)
        video_src = VideoSource.from_cfg_camera(c)
        stream = VideoStream(video_src, writer_out_path)
        streams.append(stream)

    logger.info(f"connected to {len(streams)} cameras")
    return streams


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


def recording_get_path(dir_path: Path, cam_id: int) -> Path:
    dir_path.mkdir(exist_ok=True)
    part_id = recording_path_find_part_id(dir_path)
    return dir_path.joinpath(Path(recording_path_file_name(cam_id, part_id)))


class Harvester:
    # TODO: Maybe use ABC?
    class FrameProcessorType(Protocol):
        def skipped(self) -> None: ...
        def process(self, frame: MatLike, boxes_n: list[Vec4f]) -> None: ...

    def __init__(self, config: FlowerConfig) -> None:
        self._config: FlowerConfig = config

        self._viewport: JointViewport = JointViewport(
            init_streams_from_cams(self._config.cameras, self._config.recording_dir),
            CropSettings.load_all(),
        )
        if not self._viewport.is_open():
            print("error viewport not open")
        else:
            logger.info("viewport created")

        # Load the YOLO26 model
        model_path = "yolo26n.pt"
        self._model: YOLO = YOLO(model_path)
        logger.info(f"done loading model {model_path}")

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
                logger.error(f"_viewport.read failed {e}")
                continue
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
