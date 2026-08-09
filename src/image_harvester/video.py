from __future__ import annotations

from threading import Lock
import logging
from dataclasses import dataclass
from ipaddress import IPv4Address
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import time
from typing import Callable

import cv2
from cv2.typing import MatLike

from image_harvester.config import Camera
from image_harvester.logs import logger_init

URIType = str | int

logger = logger_init()


@dataclass
class VideoSource:
    _uri: URIType

    def __init__(self, uri: URIType) -> None:
        self._uri = uri

    @classmethod
    def from_cfg_camera(cls, c: Camera) -> VideoSource:
        uri = c.get_uri()
        if isinstance(uri, int):
            return VideoSourceIndex(uri)
        elif isinstance(uri, IPv4Address):
            return VideoSourceRTP(
                address=uri, path=c.rstp_path, username=c.username, password=c.password
            )
        else:
            return VideoSourceLocalPath(uri)

    @property
    def uri(self) -> URIType:
        return self._uri


class VideoSourceIndex(VideoSource):
    def __init__(self, index: int) -> None:
        VideoSource.__init__(self, uri=index)


class VideoSourceLocalPath(VideoSource):
    def __init__(self, path: str | Path) -> None:
        if isinstance(path, Path):
            path = path.resolve().as_posix()
        VideoSource.__init__(self, uri=path)


class VideoSourceRTP(VideoSource):
    def __init__(
        self,
        address: str | IPv4Address,
        path: str,
        username: str,
        password: str,
    ) -> None:
        VideoSource.__init__(self, uri=f"rtsp://{username}:{password}@{address}{path}")


@dataclass(frozen=True)
class WriterConfig:
    # for some reason this stub file is not being found
    FOURCC: int = cv2.VideoWriter_fourcc(*"XVID")  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
    FPS: int = 30


# bufferless VideoCapture: https://stackoverflow.com/a/54755738/7363348
@dataclass
# TODO: Implement a simple `VideoStream` for just playing back a video, without any threading. Inherit from it and add threading
class VideoStream:
    _video_src: VideoSource
    _cap: cv2.VideoCapture
    _q: Queue[MatLike]
    _out_path: Path | None
    _render_thread_handle: Thread
    _writer: cv2.VideoWriter | None = None
    _videosource_is_video: bool = False
    _render_stop_mutex: Lock = Lock()
    _should_render__shared: bool = True

    def __init__(self, uri: VideoSource, out_path: Path | None = None) -> None:
        self._video_src = uri
        self._out_path = out_path
        self._cap = cv2.VideoCapture(self._video_src.uri)
        self._q = Queue()
        self._log("initializing ...")

        if isinstance(uri, VideoSourceLocalPath):
            self._videosource_is_video = True

        if self._out_path is not None:
            self._writer = cv2.VideoWriter(
                self._out_path,
                WriterConfig.FOURCC,
                WriterConfig.FPS,
                (self.width, self.height),
            )
            self._log(
                f"attached VideoWriter[{self._out_path}] to VideoStream {self._video_src}"
            )

        if not self._cap.isOpened():
            raise Exception(f"could not open URI {self._video_src}")

        self._log(f"initialized, writing to {out_path}...")
        self._render_thread_handle = Thread(target=self._reader)
        self._render_thread_handle.start()

    def _get_should_render(self) -> bool:
        with self._render_stop_mutex:
            return self._should_render__shared

    def _set_should_render(self, status: bool) -> None:
        with self._render_stop_mutex:
            self._should_render__shared = status

    def _reader(self) -> None:
        self._log("started _reader thread")
        read_frames: int = 0
        avaliable_frames = self._cap.get(cv2.CAP_PROP_FRAME_COUNT)

        while self._get_should_render():
            # TODO: this exception will exit the thread, handle that some way
            # TODO: this will fail due to it not being mutex locked when we call `release()`
            success, frame = self._cap.read()
            if self._videosource_is_video is True and read_frames >= avaliable_frames:
                logger.info("no more video frames left to read")
                break
            if not success:
                raise Exception(f"failed reading {self}")
            read_frames += 1

            # used for recording test footage
            if self._writer:
                self._writer.write(frame)

            if not self._q.empty():
                try:
                    _ = self._q.get_nowait()
                except Empty:
                    pass
            self._q.put(frame)
            # dirty trick to fix video playback.
            if self._videosource_is_video:
                time.sleep(0.050)

        self._cap.release()

    def _log(self, s: str, log_level: Callable[[str], None] = logging.info) -> None:
        log_level(f"VideoStream[{self._video_src}] {s}")

    def release(self) -> None:
        if self._writer:
            self._writer.release()
            self._log(f"released writing device {self._out_path}")

        self._set_should_render(False)
        self._render_thread_handle.join()
        self._log("released capture device")

    @property
    def width(self) -> int:
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self) -> int:
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def read(self) -> MatLike:
        return self._q.get(timeout=1)

    def is_open(self) -> bool:
        state = self._cap.isOpened()
        return state
