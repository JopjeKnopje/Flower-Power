from dataclasses import dataclass
from typing import Self, override

import cv2
from cv2.typing import MatLike
from ultralytics import YOLO


VideoSourceURI = str


# dirty trick hehe
class VideoSourceWeb(VideoSourceURI):
    def __new__(
        cls,
        address: str,
        path: str = "/mjpg/video.mjpg",
        username: str = "root",
        password: str = "admin",
    ) -> Self:
        return super().__new__(cls, f"http://{username}:{password}@{address}{path}")


@dataclass
class VideoStream:
    _uri: VideoSourceURI
    cap: cv2.VideoCapture
    _pixel_buf: MatLike
    _writer: cv2.VideoWriter | None

    def __init__(
        self, uri: VideoSourceURI, writer: cv2.VideoWriter | None = None
    ) -> None:
        self._writer = writer
        self._uri = uri
        self.cap = cv2.VideoCapture(self._uri)

        if not self.cap.isOpened():
            raise Exception(f"could not open URI {self._uri}")

    def get_pixels(self) -> MatLike:
        return self._pixel_buf

    def read(self) -> tuple[bool, MatLike]:
        success, self._pixel_buf = self.cap.read()

        if not success:
            raise Exception(f"failed reading {self}")

        # used for recording vids while debugging
        if self._writer is not None:
            self._writer.write(self.get_pixels())

        return success, self._pixel_buf

    def is_open(self) -> bool:
        return self.cap.isOpened()


@dataclass
class JointViewport:
    video_streams: list[VideoStream]

    def is_open(self) -> bool:
        for s in self.video_streams:
            if not s.is_open():
                return False
        return True

    def read_stream(self, id: int) -> tuple[bool, MatLike]:
        return self.video_streams[id].read()

    def read(self) -> tuple[bool, MatLike]:
        imgs: list[MatLike] = []
        success = False

        for i, _ in enumerate(self.video_streams):
            # TODO: error check
            success, img = self.read_stream(i)

            imgs.append(img)
        return success, cv2.hconcat(imgs)


# TODO: fix hconcat
# TODO: wait for all cameras in feed to come online with a set timeout
# TODO: Check the camera resolution


def main() -> None:

    # Load the YOLO26 model
    model = YOLO("yolo26n.pt")

    # TODO: Read from config
    cams: list[VideoStream] = [
        VideoStream(VideoSourceWeb("192.168.1.2")),
        VideoStream(VideoSourceWeb("192.168.1.3")),
        VideoStream(VideoSourceWeb("192.168.1.4")),
    ]

    viewport = JointViewport(cams)

    if not viewport.is_open():
        print("error viewport not open")

    # Loop through the video frames
    while viewport.is_open():
        success, frame = viewport.read()

        if success:
            # Run YOLO26 tracking on the frame, persisting tracks between frames
            result = model.track(frame, persist=True)[0]

            # Get the boxes and track IDs
            if result.boxes and result.boxes.is_track:
                boxes = result.boxes.xywh.cpu()
                track_ids = result.boxes.id.int().cpu().tolist()

                # Visualize the result on the frame
                frame = result.plot()
            # Display the annotated frame
            cv2.imshow("YOLO26 Tracking", frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # Release the video capture object and close the display window
    # cap.release()
    cv2.destroyAllWindows()
