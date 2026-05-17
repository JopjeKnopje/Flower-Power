from ultralytics import YOLO  # pyright: ignore[reportPrivateImportUsage]

import torch


def main1() -> None:
    print(torch.cuda.is_available())  # Should be True
    print(torch.version.cuda)
    print(torch.cuda.get_device_name(0))  # e.g. 'NVIDIA GeForce GTX 1660 Ti'


def main() -> None:

    model = YOLO("yolo26n.pt")
    results = model.track(source="https://youtu.be/YzcawvDGe4Y", show=True)

