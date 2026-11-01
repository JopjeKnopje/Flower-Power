import platform
import sys

from litestar.di import Provide
from torch.cuda import is_available as cuda_is_available

from core.logs import logger_init

from .flower_config import FlowerConfig
from .harvester import Accumulator, Harvester
from .server.server import FlowerServer
from .settings import settings

logger = logger_init()


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"


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

        is_headless = host_is_headless()
        yolo_device = "cuda"
        if is_headless or not cuda_is_available():
            yolo_device = "cpu"
        # TODO: inject windowing functions
        harvester.loop(acc, headless=is_headless, yolo_device=yolo_device)
        print("harvesting done")
