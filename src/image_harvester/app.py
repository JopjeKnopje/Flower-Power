import time
from contextlib import contextmanager
from queue import LifoQueue
from threading import Thread

import uvicorn
from litestar import Litestar
from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig

from image_harvester.controllers import RootController
from image_harvester.settings import config
from image_harvester.version import __version__

data_queue: LifoQueue[int] = LifoQueue()


def get_queue() -> LifoQueue[int]:
    return data_queue


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


class Server(uvicorn.Server):
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


def app() -> None:
    config = uvicorn.Config(
        app=webserver, host="127.0.0.1", port=5000, log_level="info"
    )
    server = Server(config=config)

    with server.run_in_thread():
        print("Server is started.")
        value = 0
        while True:
            print("123")
            time.sleep(1)
            value += 1
            get_queue().put(value)

        # TODO: Pass generated data to queue.
