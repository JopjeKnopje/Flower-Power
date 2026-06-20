import logging
from dataclasses import dataclass
from queue import Empty, Queue
from threading import Thread
from typing import Self
from math import sqrt

import cv2
from cv2.typing import MatLike
from ultralytics import YOLO

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

VideoSourceURI = str


# dirty trick hehe
class VideoSourceRTP(VideoSourceURI):
    def __new__(
        cls,
        address: str,
        path: str = "/axis-media/media.amp",
        username: str = "root",
        password: str = "admin",
    ) -> Self:
        return super().__new__(cls, f"rtsp://{username}:{password}@{address}{path}")


# bufferless VideoCapture: https://stackoverflow.com/a/54755738/7363348
@dataclass
class VideoStream:
    _uri: VideoSourceURI
    _cap: cv2.VideoCapture
    _writer: cv2.VideoWriter | None
    _q: Queue[MatLike]

    def __init__(
        self, uri: VideoSourceURI, writer: cv2.VideoWriter | None = None
    ) -> None:
        self._writer = writer
        self._uri = uri
        self._cap = cv2.VideoCapture(self._uri)
        self._q = Queue()

        if self._writer:
            # TODO: Get VideoWriter filename
            logger.info(f"VideoWriter attached to VideoStream{uri}")

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


def main() -> None:
    # Load the YOLO26 model
    model = YOLO("yolo26n.pt")
    fourcc = cv2.VideoWriter_fourcc(*"XVID")

    cams: list[VideoStream] = [
        VideoStream(
            VideoSourceRTP("192.168.1.2"),
            cv2.VideoWriter("recordings/output-2.avi", fourcc, 30.0, (1280, 960)),
        ),
        VideoStream(
            VideoSourceRTP("192.168.1.3"),
            cv2.VideoWriter("recordings/output-3.avi", fourcc, 30.0, (1280, 960)),
        ),
        VideoStream(
            VideoSourceRTP("192.168.1.4"),
            cv2.VideoWriter("recordings/output-4.avi", fourcc, 30.0, (1280, 960)),
        ),
    ]

    print(f"initiaized {len(cams)} cameras")

    viewport = JointViewport(cams)

    tracked_objects: dict[int, int] = {}
    if not viewport.is_open():
        print("error viewport not open")

    # Loop through the video frames
    while viewport.is_open():
        try:
            frame = viewport.read()
        except Exception as e:
            logger.error(e)
            continue

        # Run YOLO26 tracking on the frame, persisting tracks between frames
        # TODO: read about `classes=[0]`, it does however tell the model to only detect humans.
        result = model.track(frame, persist=True, classes=[0])[0]

        # Get the boxes and track IDs
        if result.boxes and result.boxes.is_track:
            boxes = result.boxes.xywh.cpu()
            boxes_cls = result.boxes.cls.cpu()
            track_ids = result.boxes.id.int().cpu().tolist()

            for box, track_id, box_cls in zip(boxes, track_ids, boxes_cls):
                x, y, w, h = box
                if model.names[int(box_cls)] != "person":
                    continue
                object_diagonal = sqrt(w**2 + h**2)

                print(f"object {track_id} size {object_diagonal}")
                tracked_objects[track_id] = int(object_diagonal)

            # Visualize the result on the frame
            frame = result.plot()
        height, width, _ = frame.shape

        # Display the annotated frame
        cv2.imshow(f"Flower Power @ {width}x{height}", frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release the video capture object and close the display window
    # TODO: Close video caps
    cv2.destroyAllWindows()
