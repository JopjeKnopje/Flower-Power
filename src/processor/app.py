from websockets.sync.client import connect

from core.flower_api import FlowerAPI
from core.logs import logger_init
from core.models.models import BoxesModel
from image_harvester.flower_config import FlowerConfig
from processor.processor import PeopleCounter, Processor

logger = logger_init()


def loop(proc: Processor, boxes: BoxesModel) -> None:
    if boxes.boxes:
        proc.process(boxes.boxes)
    else:
        proc.skipped()


def app() -> None:
    """
    Run the flower code
    """

    config = FlowerConfig.read()
    print(config)

    # harvester_api = ImageHarvesterAPI("http://192.168.0.135:5000")
    flower_api = FlowerAPI(config.flower_endpoint)
    _ = PeopleCounter(flower_api)

    with connect("ws://192.168.0.10:5000") as ws:
        while True:
            print("waiting for data")
            data = ws.recv()
            print(f"received {data}")

    # while True:
    #     boxes = harvester_api.get_boxes()
    #     if len(boxes) == 0:
    #         continue
    #     loop(proc, boxes[0])
    #     # TODO: Try and see if we can use websocket for this.
    #     # print(boxes)
    #     time.sleep(0.5)
