import cv2

from ultralytics import YOLO
from PIL import Image
import numpy as np
from dataclasses import dataclass

from shapes import Color, Line, Point


@dataclass
class VideoStream:
    _url: str
    address: str
    cap: cv2.VideoCapture

    def __init__(self, address: str) -> None:
        self.address = address
        # TODO: Read credentials from env?
        self._url = f"http://root:admin@{self.address}/mjpg/video.mjpg"

    def start(self) -> None:
        self.cap = cv2.VideoCapture(self._url)

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


def main() -> None:

    # Load the YOLO26 model
    model = YOLO("yolo26n.pt")

    # TODO: Read from config
    cams: list[VideoStream] = [
        VideoStream("192.168.0.2"),
        VideoStream("192.168.0.3"),
    ]

    for c in cams:
        c.start()

    viewport = JointViewport(cams)

    if not viewport.is_open():
        print("error viewport not open")

    for idx, c in enumerate(cams):
        success, img = c.cap.read()
        _ = cv2.imwrite(f"capture{idx}.jpg", img)

    img0 = Image.open("capture0.jpg")
    img1 = Image.open("capture1.jpg")

    width = img0.size[0]

    img2 = Image.new("RGB", (width * 2, img0.size[1]))

    img2.paste(img0, (0, 0))
    img2.paste(img1, (width, 0))

    open_cv_image = np.array(img2)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    _ = cv2.imwrite("joint.jpg", open_cv_image)

    return

    # Loop through the video frames
    while viewport.is_open():
        # Read a frame from the video
        success, frame = cap.read()

        flower_location.draw(frame)

        if success:
            # Run YOLO26 tracking on the frame, persisting tracks between frames
            result = model.track(frame, persist=True)[0]

            # Get the boxes and track IDs
            if result.boxes and result.boxes.is_track:
                boxes = result.boxes.xywh.cpu()
                track_ids = result.boxes.id.int().cpu().tolist()

                # Visualize the result on the frame
                frame = result.plot()

                # Plot the tracks
                for box, track_id in zip(boxes, track_ids):
                    x, y, w, h = box

                    p = Point((int(x), int(y)))
                    proj = find_line(p, flower_location)
                    proj.set_color(Color.LIGHT_BLUE)
                    proj.draw(frame)

                    # track = track_history[track_id]
                    # track.append((float(x), float(y)))  # x, y center point
                    # if len(track) > 30:  # retain 30 tracks for 30 frames
                    #     track.pop(0)

                    # # Draw the tracking lines
                    # points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                    # cv2.polylines(
                    #     frame,
                    #     [points],
                    #     isClosed=False,
                    #     color=(230, 230, 230),
                    #     thickness=10,
                    # )

            # Display the annotated frame
            cv2.imshow("YOLO26 Tracking", frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break

    # Release the video capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()
