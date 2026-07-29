from __future__ import annotations
from dataclasses import dataclass
import logging
import platform
import sys
import time
from typing import Callable, Literal, Protocol
import httpx

import cv2
from cv2.typing import MatLike
from torch import Tensor, torch
from ultralytics import YOLO
from pathlib import Path

from ultralytics.engine.results import Boxes

from image_harvester.config import Config
from image_harvester.logger import logger_init
from image_harvester.video import VideoSource, VideoStream

logger = logger_init()
# TODO: Fix this
logging.getLogger("httpx").setLevel("CRITICAL")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").propagate = False


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
        logging.info(f"send request {r_str}")

        log_str = f"controller HTTP: {r.status_code}"
        if r.status_code >= 400:
            logging.warning(log_str)
        elif r.status_code:
            logging.info(log_str)


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



def host_is_headless() -> bool:
    # when we're running on rpi its headless
    return sys.platform == 'linux' or platform.machine == 'aarch64'



class Harvester:
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



    def _init_streams(self, cfg: Config) -> list[VideoStream]:
        streams: list[VideoStream] = []

        for i, c in enumerate(cfg.cameras):
            writer_out_path = None
            if cfg.recording_dir:
                writer_out_path = recording_get_path(Path(f"{cfg.recording_dir}"), i)
            video_src = VideoSource.from_cfg_camera(c)
            stream = VideoStream(video_src, writer_out_path)
            streams.append(stream)

        logger.info(f"connected to {len(streams)} cameras")
        return streams

    def loop(self, callback: SupportsFrameCB, headless: bool = False, yolo_device: Literal["cpu", "cuda"] = "cuda") -> None:
        while self._viewport.is_open():
            try:
                frame = self._viewport.read()
            except Exception as e:
                logger.error(e)
                continue
            # TODO: set cpu option based on cli parameter
            result = self._model.track(
                frame,
                verbose=self._config.yolo_verbose,
                persist=True,
                classes=[0],
                device=yolo_device
            )[0]

            # Get the boxes and track IDs
            if result.boxes and result.boxes.is_track:
                boxes = result.boxes.xywh.cpu()
                # TODO: Remove boxes_cls since we already know we're just checking for a person, when we set `classes=[0]`
                boxes_cls = result.boxes.cls.cpu()
                track_ids = result.boxes.id.int().cpu().tolist()

                # TODO: Measure time it takes to call isinstance
                if isinstance(boxes, Tensor):
                    callback(boxes)

                # Visualize the result on the frame
                frame = result.plot()
                height, width, _ = frame.shape

                # Display the annotated frame
                if not headless:
                    cv2.imshow(f"Flower Power @ {width}x{height}", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        self._viewport.release()
        if not headless:
            cv2.destroyAllWindows()


class SupportsFrameCB(Protocol):
    def __call__(self, boxes: Tensor) -> None:
        ...


class Processor:
    # this should potentially take a web-requestor to talk to the flower.
    def __init__(self) -> None:
        self._process_counter: int = 0

    def process_frame(self, boxes: Tensor) -> None:
        # for box, track_id, box_cls in zip(boxes, track_ids, boxes_cls):
        #     x, y, w, h = box
        #     object_height = h
        #     tracked_objects.append(int(object_height))

        logger.warning(f"called callback {self._process_counter}")

        self._process_counter += 1



def main() -> None:

    # get cli args for cuda or cpu mode (also read them from config file?)

    config = Config.read()
    print(config)
    harvester = Harvester(Config.read())

    prc = Processor()

    harvester.loop(prc.process_frame, yolo_device="cuda")




    # time_old = time.time() + config.flower_interval

