from litestar.di import Provide

from image_harvester.processor import TestProcessor
from image_harvester.server.server import FlowerServer
from image_harvester.settings import settings
from processor.flower_config import FlowerConfig
from processor.harvester import Harvester


def app() -> None:
    config = FlowerConfig.read()
    harvester = Harvester(config)

    proc = TestProcessor()

    processor_dependencies = {"test_model": Provide(proc.get_model)}

    server = FlowerServer(
        host=settings.server_host,
        port=settings.server_port,
        server_dependencies=processor_dependencies,
    )

    with server.run_in_thread():
        print("Server is started.")

        # api = Flower("http:123")
        # proc = PeopleCounter(api)
        print("harvesting looping...")

        harvester.loop(proc)

        print("harvesting done")
        # TODO: Pass generated data to queue.
