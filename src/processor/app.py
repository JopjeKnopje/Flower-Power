from core.flower_api import FlowerAPI
from core.logs import logger_init
from core.models.models import BoxesModel
from core.receiver_ws import ReceiverWS
from image_harvester.flower_config import FlowerConfig
from processor.processor import PeopleCounter

logger = logger_init()


def app() -> None:
    """
    Run the flower code
    """
    config = FlowerConfig.read()
    print(config)

    flower_api = FlowerAPI(config.flower_endpoint)
    proc = PeopleCounter(flower_api)

    # Real gnarly
    def receive_cb(model: BoxesModel) -> None:
        logger.info(f"received {model}")
        if model.boxes is None:
            proc.skipped()
            return
        proc.process(model.boxes)

    # TODO: Read from config
    ws = ReceiverWS(cb=receive_cb, image_harvester_host="192.168.0.10:5000")
    ws.loop()
