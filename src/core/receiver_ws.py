from collections.abc import Callable

from websockets.sync.client import connect

from core.models.models import BoxesModel


class ReceiverWS:
    def __init__(
        self, cb: Callable[[BoxesModel], None], image_harvester_host: str
    ) -> None:
        self._cb: Callable[[BoxesModel], None] = cb
        self._image_harvester_host: str = f"ws://{image_harvester_host}"

    def loop(self) -> None:
        with connect(self._image_harvester_host) as ws:
            while True:
                data = ws.recv(decode=True)
                model = BoxesModel.parse(data)
                self._cb(model)
