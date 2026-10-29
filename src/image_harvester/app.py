import time
from contextlib import contextmanager
from threading import Thread

import uvicorn
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig

from image_harvester.controllers import RootController
from image_harvester.settings import config
from image_harvester.version import __version__


def app() -> Litestar:
    openapi_config = OpenAPIConfig(
        version=__version__, title="FlowerPower ImageHarvester API"
    )

    app = Litestar(
        route_handlers=[RootController],
        debug=config.debug,
        openapi_config=openapi_config,
    )

    # current_loop = asyncio.get_running_loop()
    # _ = current_loop.create_task(query_router(3))

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


def runner() -> None:
    config = uvicorn.Config(app=app, host="127.0.0.1", port=5000, log_level="info")
    server = Server(config=config)

    with server.run_in_thread():
        print("Server is started.")
        while True:
            print("123")
            time.sleep(1)

        print("Server exited.")
