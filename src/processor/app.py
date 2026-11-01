import time

from core.flower_api import Flower
from core.image_harvester_api import ImageHarvesterAPI
from core.logs import logger_init
from core.models.models import BoxesModel
from image_harvester.flower_config import FlowerConfig
from processor.processor import PeopleCounter, Processor

logger = logger_init()


def loop(proc: Processor, boxes: BoxesModel) -> None:
    if boxes.box:
        proc.process(boxes.box)
    else:
        proc.skipped()


def app() -> None:
    """
    Run the flower code
    """

    config = FlowerConfig.read()
    print(config)

    harvester_api = ImageHarvesterAPI("http://127.0.0.1:5000")
    flower = Flower(config.flower_endpoint)
    proc = PeopleCounter(flower)

    while True:
        boxes = harvester_api.get_boxes()[0]
        loop(proc, boxes)
        # TODO: Try and see if we can use websocket for this.
        print(boxes)
        time.sleep(0.5)
