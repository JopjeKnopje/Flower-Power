from core.flower_api import Flower
from core.logs import logger_init
from core.models.models import BoxesModel
from image_harvester.flower_config import FlowerConfig
from processor.processor import Processor

logger = logger_init()


def loop(_proc: Processor, _boxes: BoxesModel) -> None: ...


def app() -> None:
    """
    Run the flower code
    """

    config = FlowerConfig.read()
    print(config)

    _ = Flower(config.flower_endpoint)

    while True:
        # 1. get data from image_harvester
        # 2. get data from image_harvester
        ...
