from ultralytics import YOLO  # pyright: ignore[reportPrivateImportUsage]

import torch


def main1() -> None:
    print(torch.cuda.is_available())  # Should be True
    print(torch.version.cuda)
    print(torch.cuda.get_device_name(0))  # e.g. 'NVIDIA GeForce GTX 1660 Ti'


def main() -> None:
    main1()

    # Create a new YOLO model from scratch
    model = YOLO("yolo26n.yaml")

    # # Load a pretrained YOLO model (recommended for training)
    # model = YOLO("yolo26n.pt")

    # Train the model using the 'coco8.yaml' dataset for 3 epochs
    # results = model.train(data="coco8.yaml", epochs=3, device="cpu")
    results = model.train(data="coco8.yaml", epochs=3)

    # Evaluate the model's performance on the validation set
    results = model.val()

    # Perform object detection on an image using the model
    results = model("https://ultralytics.com/images/bus.jpg")

    # Export the model to ONNX format
    success = model.export(format="onnx")


main()
