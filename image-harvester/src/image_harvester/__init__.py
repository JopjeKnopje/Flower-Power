from collections import defaultdict
import random
from typing import Self

import cv2
import numpy as np

from ultralytics import YOLO

from image_harvester_test import find_line
from shapes import Color, Line, Point


def main() -> None:

    # Load the YOLO26 model
    model = YOLO("yolo26n.pt")

    # Open the video file
    video_path = "test-vids/top-down.mp4"
    cap = cv2.VideoCapture(video_path)

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # which is a simple line for now (we should actually use a point for this)
    flower_location = Line(
        [200, frame_height - 25], [frame_width - 200, frame_height - 25], 0xFFFF11
    )
    flower_location.set_color(Color.RED)

    # Loop through the video frames
    while cap.isOpened():
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
