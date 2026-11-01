import platform
import sys

from cyclopts import App
from litestar import Litestar
from torch.cuda import is_available as cuda_is_avaliable

from core.flower_api import Flower
from core.logs import logger_init
from image_harvester.flower_config import FlowerConfig
from image_harvester.harvester import Harvester
from processor.processor import PeopleCounter

cli = App()

logger = logger_init()


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"


class RootController:
    pass


# TODO: Add gui override
@cli.default
def run() -> Litestar:
    """
    Run the flower code
    """

    config = FlowerConfig.read()
    print(config)
    harvester = Harvester(config)

    api = Flower(config.flower_endpoint)

    # TODO Pass this algo at runtime
    # proc = CloseProcessor(api)
    proc = PeopleCounter(api)
    # proc = None

    is_headless = host_is_headless()
    yolo_device = "cuda"
    if is_headless or not cuda_is_avaliable():
        yolo_device = "cpu"

    harvester.loop(proc, yolo_device=yolo_device, headless=is_headless)

    serv = Litestar(route_handlers=[RootController])
    return serv

    # if len(proc._data_raw) != 0:
    #     with open("office_people.raw", "wb") as f:
    #         pickle.dump(proc._data_raw, f)
    # if len(proc._sma_output_list) != 0:
    #     with open("office_people.sma", "wb") as f:
    #         pickle.dump(proc._sma_output_list, f)
