import platform
import sys

from litestar.di import Provide

from core.logs import logger_init
from processor.processor import TestProcessor

from .flower_config import FlowerConfig
from .harvester import Harvester
from .server.server import FlowerServer
from .settings import settings

logger = logger_init()


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"


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
