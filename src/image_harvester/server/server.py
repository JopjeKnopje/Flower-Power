import time
from contextlib import contextmanager
from threading import Thread

import uvicorn
from litestar import Litestar
from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig

from image_harvester.queue import get_queue
from image_harvester.server.controllers import RootController
from image_harvester.settings import config
from image_harvester.version import __version__


def webserver() -> Litestar:
    openapi_config = OpenAPIConfig(
        version=__version__, title="FlowerPower ImageHarvester API"
    )

    app = Litestar(
        dependencies={"get_queue": Provide(get_queue)},
        route_handlers=[RootController],
        debug=config.debug,
        openapi_config=openapi_config,
    )

    return app


class FlowerServer(uvicorn.Server):
    def __init__(self, host: str, port: int, log_level: str | int = "info") -> None:
        config = uvicorn.Config(
            app=webserver, host=host, port=port, log_level=log_level
        )
        super().__init__(config)

    def install_signal_handlers(self):
        pass

    @contextmanager
    def run_in_thread(self):
        thread = Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit: bool = True
            thread.join()
