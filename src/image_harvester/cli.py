from enum import Enum, StrEnum
import importlib
import platform
import sys

from cyclopts import App
from torch.cuda import is_available as cuda_is_avaliable

import image_harvester
from image_harvester.cropper import Cropper
from image_harvester.flower_api import Flower
from image_harvester.flower_config import FlowerConfig
from image_harvester.harvester import Harvester
from image_harvester.logs import logger_init
from image_harvester.processor import AbstractProcessor, PeopleCounter, Processor

cli = App()

logger = logger_init()


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"


@cli.command
def crop() -> None:
    """
    Open a UI in which you can crop camera feeds and save them into a JSON file.
    """

    if host_is_headless():
        raise RuntimeError("cannot open gui on headless device")

    config = FlowerConfig.read()
    print(config)

    crop = Cropper(config.cameras)
    crop.loop()


def list_processors() -> list[str]:
    return [cls.__name__ for cls in AbstractProcessor.__subclasses__()]

ProcessorName = StrEnum("ProcessorName", list_processors())

def get_processor_type_by_name(name: ProcessorName) -> type[AbstractProcessor]:
    return getattr(importlib.import_module("image_harvester.processor"), name)  # pyright: ignore[reportAny]



# TODO: Add gui override
@cli.default
def run(processor: ProcessorName) -> None:
    """
    Run the flower code
    """

    config = FlowerConfig.read()
    print(config)
    harvester = Harvester(config)

    api = Flower(config.flower_endpoint)

    proc = get_processor_type_by_name(processor)(api)

    is_headless = host_is_headless()
    yolo_device = "cuda"
    if is_headless or not cuda_is_avaliable():
        yolo_device = "cpu"

    harvester.loop(proc, yolo_device=yolo_device, headless=is_headless)

    # if len(proc._data_raw) != 0:
    #     with open("office_people.raw", "wb") as f:
    #         pickle.dump(proc._data_raw, f)
    # if len(proc._sma_output_list) != 0:
    #     with open("office_people.sma", "wb") as f:
    #         pickle.dump(proc._sma_output_list, f)
