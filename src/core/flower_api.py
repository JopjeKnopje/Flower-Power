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
    target_mm: float | None = None


class Flower:
    type Endpoint = Literal["/people", "/main", "/status", "/move", "/stop", "/cnt"]

    def __init__(self, host: str) -> None:
        # TODO: Error handle the endpoint not containing http?
        self._host: str = host

    def _http_get(
        self, endpoint: Endpoint, params: dict[str, str] | str | None = None
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

    def main_mode(self, enable: bool) -> Status:

        if enable:
            args = "on"
        else:
            args = "off"
        content = self._http_get("/main", args).content
        return self._decode(content)

    def people(self, value: int) -> Status:
        _ = self.main_mode(True)
        content = self._http_get("/people", {"n": str(value)}).content
        logger.info(f"response {content.decode()}")
        return self._decode(content)

    def move(self, pos: int) -> Status:
        content = self._http_get("/move", {"band": str(pos)}).content
        return self._decode(content)

    def stop(self) -> Status:
        content = self._http_get("/stop").content
        return self._decode(content)
