from dataclasses import dataclass
from typing import Literal

import httpx
import msgspec
from httpx import Response

from core.logs import logger_init

logger = logger_init()


@dataclass
class Status:
    adc: int
    auto: bool
    stroke_mm: float
    fire: list[int]
    target_mm: float | None = None


class FlowerAPI:
    # type _Endpoint = Literal["/people", "/main", "/status", "/move", "/stop", "/cnt"]
    type _Endpoint = str

    def __init__(self, host: str) -> None:
        # TODO: Error handle the endpoint not containing http?
        self._host: str = f"http://{host}"

    def _http_get(
        self, endpoint: _Endpoint, params: dict[str, str] | str | None = None
    ) -> Response:
        resp = httpx.get(f"{self._host}{endpoint}", params=params).raise_for_status()
        return resp

    @staticmethod
    def _decode(content: bytes) -> Status:
        return msgspec.json.decode(content, type=Status, strict=False)

    def status(self) -> Status:
        content = self._http_get("/status").content
        return self._decode(content)

    def count(self, value: int) -> Status:
        content = self._http_get("/cnt", {"n": str(value)}).content
        return self._decode(content)

    def fire(self, stamen_n: int | Literal["all"], duration_ms: int = 200) -> Status:
        """
        spew fire from one or all of the stamen

        :stamen_n number of the stamen `0-4` or `"all"` to fire
        :duration_ms duration of the fire
        """

        args = {"n": str(stamen_n), "ms": str(duration_ms)}
        content = self._http_get("/fire", args).content
        return self._decode(content)

    def main_mode(self, state: bool) -> Status:
        """
        enable or disable main-mode on the flower

        state: state
        """
        if state:
            args = "on"
        else:
            args = "off"
        # TODO: find other way to pass this along
        content = self._http_get(f"/main?{args}").content
        return self._decode(content)

    def people(self, value: int) -> Status:
        """
        send the amount of detected people to the flower controller.
        used in main-mode

        value: amount of people
        """
        _ = self.main_mode(True)
        content = self._http_get("/people", {"n": str(value)}).content
        logger.info(f"response {content.decode()}")
        return self._decode(content)

    def move(self, pos: int) -> Status:
        """
        move the flower petals into a position

        :pos valid input `0-9`
        """

        content = self._http_get("/move", {"band": str(pos)}).content
        return self._decode(content)

    def stop(self) -> Status:
        content = self._http_get("/stop").content
        return self._decode(content)
