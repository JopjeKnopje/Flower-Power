from ultralytics import YOLO  # pyright: ignore[reportPrivateImportUsage]
import cv2


def main() -> None:
    # Load the YOLO26 model
    model = YOLO("yolo26n.pt")

    # Open the video file
    cap = cv2.VideoCapture("test-vids/video1.mp4")

    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()

        if success:
            # Run YOLO26 tracking on the frame, persisting tracks between frames
            result = model.track(frame, persist=True)[0]

            object_count: int = 0

            # super gnarly
            for box in result.boxes:
                if model.names[int(box.cls)] == "person":
                    object_count += 1

            print(f"people count {object_count}")
            annotated_frame = result.plot()

            # Display the annotated frame
            cv2.imshow("YOLO26 Tracking", annotated_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            break

    # Release the video capture object and close the display window
    cap.release()
    cv2.destroyAllWindows()
