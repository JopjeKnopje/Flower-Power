from dataclasses import dataclass
from enum import StrEnum


import httpx
from httpx import Response
import msgspec


@dataclass
class Status:
    adc: int
    auto: bool
    stroke_mm: float
    target_mm: float | None = None


class Flower:
    class _Endpoints(StrEnum):
        people = "/people"
        main = "/main"
        status = "/status"
        move = "/move"
        stop = "/stop"
        cnt = "/cnt"

    def __init__(self, endpoint: str) -> None:
        # TODO: Error handle the endpoint not containing http?
        self._endpoint: str = endpoint

    def _http_get(
        self, path: str, params: dict[str, str] | str | None = None
    ) -> Response:
        resp = httpx.get(f"{self._endpoint}{path}", params=params).raise_for_status()
        return resp

    @staticmethod
    def _decode(content: bytes) -> Status:
        return msgspec.json.decode(content, type=Status, strict=False)

    def status(self) -> Status:
        content = self._http_get(self._Endpoints.status).content
        return self._decode(content)

    def count(self, value: int) -> Status:
        content = self._http_get(self._Endpoints.cnt, {"n": str(value)}).content
        return self._decode(content)

    def main_mode(self, enable: bool) -> Status:
        if enable:
            args = "on"
        else:
            args = "off"
        content = self._http_get(self._Endpoints.main, args).content
        return self._decode(content)

    def people(self, value: int) -> Status:
        content = self._http_get(self._Endpoints.people, {"n": str(value)}).content
        print(content)
        return self._decode(content)

    def move(self, pos: int) -> Status:
        content = self._http_get(self._Endpoints.move, {"band": str(pos)}).content
        return self._decode(content)

    def stop(self) -> Status:
        content = self._http_get(self._Endpoints.stop).content
        return self._decode(content)
