from time import sleep
from core.flower_api import FlowerAPI
from core.image_harvester_api import ImageHarvesterAPI
from core.logs import logger_init
from core.models.models import BoxesModel
from image_harvester.flower_config import FlowerConfig
from processor.processor import PeopleCounter

logger = logger_init()


def app() -> None:
    """
    Run the flower code
    """
    config = FlowerConfig.read()
    print(config)

    flower_api = FlowerAPI("192.168.0.42")
    camera = ImageHarvesterAPI("192.168.0.135:5000")
    proc = PeopleCounter(flower_api)

    # Real gnarly
    def receive_cb(model: BoxesModel) -> None:
        logger.info(f"received {model}")
        if model.boxes is None:
            proc.skipped()
            return
        proc.process(model.boxes)

    while True:
        try:
            count = camera.get_people_count()
            proc.update_count(count)
            sleep(1)
        except Exception as e:
            print(e)
