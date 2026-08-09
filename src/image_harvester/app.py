import platform
import sys

from cyclopts import App
from torch.cuda import is_available as cuda_is_avaliable

from image_harvester.config import Config
from image_harvester.flower_api import Flower
from image_harvester.harvester import Harvester
from image_harvester.logs import logger_init
from image_harvester.processor import Processor

logger = logger_init()
cli = App()


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"


@cli.command
def calibrate() -> None: ...


@cli.default
def run() -> None:

    config = Config.read()
    print(config)
    harvester = Harvester(Config.read())

    api = Flower(config.flower_endpoint)

    proc = Processor(api)

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


def main() -> None:
    cli()
