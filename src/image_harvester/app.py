from litestar.di import Provide

from core.accumulator import Accumulator
from core.logs import logger_init
from image_harvester.settings import settings

from .flower_config import FlowerConfig
from .harvester import Harvester
from .server.server import FlowerServer

logger = logger_init()


def app() -> None:
    config = FlowerConfig.read()
    harvester = Harvester(config)

    acc = Accumulator()

    processor_dependencies = {"accumulator": Provide(acc.get)}
    server = FlowerServer(
        host=settings.server_host,
        port=settings.server_port,
        server_dependencies=processor_dependencies,
    )

    logger.info("Server is started.")
    with server.run_in_thread():
        logger.info("harvesting looping...")

        # TODO: inject windowing functions
        harvester.loop(
            acc,
            yolo_device=settings.yolo_device,
            yolo_verbose=settings.yolo_verbose,
            headless=settings.headless,
        )
        print("harvesting done")
