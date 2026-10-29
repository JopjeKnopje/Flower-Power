from image_harvester.processor import TestProcessor
from image_harvester.server.server import FlowerServer
from image_harvester.settings import settings
from processor.flower_config import FlowerConfig
from processor.harvester import Harvester


def app() -> None:
    server = FlowerServer(host=settings.server_host, port=settings.server_port)

    config = FlowerConfig.read()
    print(config)
    harvester = Harvester(config)

    with server.run_in_thread():
        print("Server is started.")

        proc = TestProcessor()
        print("harvesting looping...")

        harvester.loop(proc)

        print("harvesting done")
        # TODO: Pass generated data to queue.
