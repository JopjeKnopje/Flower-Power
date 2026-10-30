import time
from contextlib import contextmanager
from threading import Thread

import uvicorn
from litestar import Litestar
from litestar.openapi.config import OpenAPIConfig
from litestar.types import Dependencies

from image_harvester.server.controllers import RootController
from image_harvester.settings import settings
from image_harvester.version import __version__


# Kinda dirty but we need to somehow inject the `model_cbs` into our litestar instance
class FlowerServer(uvicorn.Server):
    def __init__(
        self,
        host: str,
        port: int,
        server_dependencies: Dependencies,
        log_level: str | int = "info",
    ) -> None:
        config = uvicorn.Config(
            app=self.webserver, host=host, port=port, log_level=log_level
        )
        super().__init__(config)
        self._server_dependencies: Dependencies = server_dependencies

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

    def webserver(self) -> Litestar:
        openapi_config = OpenAPIConfig(
            version=__version__, title="FlowerPower ImageHarvester API"
        )

        app = Litestar(
            dependencies=self._server_dependencies,
            route_handlers=[RootController],
            debug=settings.debug,
            openapi_config=openapi_config,
        )

        return app
