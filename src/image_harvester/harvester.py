from __future__ import annotations
import asyncio
from dataclasses import dataclass
from ipaddress import IPv4Address
import logging
import math
import pathlib
import time
import httpx
from queue import Empty, Queue
from threading import Thread
from typing import Self
from math import sqrt

import cv2
from cv2.typing import MatLike
from ultralytics import YOLO

from image_harvester.config import Config, Camera
from image_harvester.logger import logger_init

logger = logger_init()
logging.getLogger("httpx").setLevel("CRITICAL")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").propagate = False

class VideoSource(str):
    def __new__(cls, c: Camera) -> VideoSource:
        uri = c.get_uri()
        if isinstance(uri, IPv4Address):
            return VideoSourceRTP(uri, c.rstp_path, c.username, c.password)
        return VideoSourceURI(uri)


class VideoSourceURI(VideoSource):
    def __new__(cls, path: str | pathlib.Path) -> Self:
        if isinstance(path, pathlib.Path):
            path = path.resolve().as_posix()
        return str.__new__(cls, path)


class VideoSourceRTP(VideoSource):
    def __new__(
        cls,
        address: str | IPv4Address,
        path: str,
        username: str,
        password: str,
    ) -> Self:
        return str.__new__(cls, f"rtsp://{username}:{password}@{address}{path}")


# bufferless VideoCapture: https://stackoverflow.com/a/54755738/7363348
@dataclass
class VideoStream:
    _uri: VideoSource
    _cap: cv2.VideoCapture
    _writer: cv2.VideoWriter | None
    _q: Queue[MatLike]

    def __init__(self, uri: VideoSource, writer: cv2.VideoWriter | None = None) -> None:
        self._uri = uri
        self._writer = writer
        self._cap = cv2.VideoCapture(self._uri)
        self._q = Queue()

        if self._writer:
            # TODO: Get VideoWriter filename
            logger.info(f"VideoWriter attached to VideoStream{self._uri}")

        if not self._cap.isOpened():
            raise Exception(f"could not open URI {self._uri}")

        Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        logger.info("started _reader thread")
        while True:
            # TODO: this exception will exit the thread, handle that some way
            success, frame = self._cap.read()
            if not success:
                raise Exception(f"failed reading {self}")

            # used for recording test footage
            if self._writer is not None:
                self._writer.write(frame)

            if not self._q.empty():
                try:
                    _ = self._q.get_nowait()
                except Empty:
                    pass
            self._q.put(frame)

    def read(self) -> MatLike:
        return self._q.get()

    def is_open(self) -> bool:
        return self._cap.isOpened()


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

#TODO: Make this actually something smaert
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
    if value > 0 and value < 9:
        r_str = f"{endpoint}/move?band={value}"
        r = httpx.request("GET", url=r_str)
        logging.info(f"send request {r_str}")

        log_str = f"controller HTTP: {r.status_code}"
        if r.status_code >= 400:
            logging.warning(log_str)
        elif r.status_code:
            logging.info(log_str)



def harvester() -> None:
    # Load the YOLO26 model
    model = YOLO("yolo26n.pt")
    fourcc = cv2.VideoWriter_fourcc(*"XVID")

    config = Config.read()

    streams: list[VideoStream] = []

    for c in config.cameras:
        streams.append(VideoStream(VideoSource(c)))
    logger.info(f"connected to {len(streams)} cameras")

    viewport = JointViewport(streams)

    if not viewport.is_open():
        print("error viewport not open")

    time_old = time.time() + 5

    # Loop through the video frames
    while viewport.is_open():
        tracked_objects: list[int] = []

        try:
            frame = viewport.read()
        except Exception as e:
            logger.error(e)
            continue

        # Run YOLO26 tracking on the frame, persisting tracks between frames
        # TODO: read about `classes=[0]`, it does however tell the model to only detect humans.
        result = model.track(
            frame, verbose=config.yolo_verbose, persist=True, classes=[0]
        )[0]

        # Get the boxes and track IDs
        if result.boxes and result.boxes.is_track:
            boxes = result.boxes.xywh.cpu()
            boxes_cls = result.boxes.cls.cpu()
            track_ids = result.boxes.id.int().cpu().tolist()

            for box, track_id, box_cls in zip(boxes, track_ids, boxes_cls):
                x, y, w, h = box
                if model.names[int(box_cls)] != "person":
                    continue
                object_diagonal = h
                tracked_objects.append(int(object_diagonal))


            # Visualize the result on the frame
            frame = result.plot()
        height, width, _ = frame.shape
        # TODO Get from camera property

        # Display the annotated frame
        cv2.imshow(f"Flower Power @ {width}x{height}", frame)

        value = calculate_frames(height, tracked_objects)

        delta = time.time() - time_old
        if delta > 3.0:
            make_request(config.flower_endpoint, value)
            time_old = time.time()

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release the video capture object and close the display window
    # TODO: Close video caps
    cv2.destroyAllWindows()
