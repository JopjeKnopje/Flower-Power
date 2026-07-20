from __future__ import annotations
from dataclasses import dataclass
import logging
import time
import httpx

import cv2
from cv2.typing import MatLike
from ultralytics import YOLO
from pathlib import Path

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
        logger.info(f"frame {ratio}")
        if ratio > close_threshold:
            close_count += 2
        else:
            away_count += 1

    value = int(close_count + away_count)
    logger.info(f"value {value} close_count {close_count} away_count {away_count}")

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




def harvester() -> None:
    config = Config.read()
    streams: list[VideoStream] = []

    for i, c in enumerate(config.cameras):
        writer_out_path = None
        if config.recording_dir:
            writer_out_path = recording_get_path(Path(f"{config.recording_dir}"), i)
        stream = VideoStream(VideoSource.from_cfg_camera(c), writer_out_path)
        streams.append(stream)

    logger.info(f"connected to {len(streams)} cameras")

    viewport = JointViewport(streams)

    if not viewport.is_open():
        print("error viewport not open")

    logger.info("viewport created")

    time_old = time.time() + config.flower_interval

    # Load the YOLO26 model
    model_path = "yolo26n.pt"
    model = YOLO(model_path)
    logger.info(f"done model {model_path}")

    # Loop through the video frames
    while viewport.is_open():
        try:
            frame = viewport.read()
        except Exception as e:
            logger.error(e)
            continue

        logger.info("read from viewport")

        tracked_objects: list[int] = []

        # Run YOLO26 tracking on the frame, persisting tracks between frames
        # TODO: read about `classes=[0]`, it does however tell the model to only detect humans.
        result = model.track(frame, verbose=config.yolo_verbose)

    # Release the video capture object and close the display window
    # TODO: Close video caps
    viewport.release()
    cv2.destroyAllWindows()
