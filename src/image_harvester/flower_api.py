from dataclasses import dataclass
from enum import StrEnum

import httpx
from httpx import Response
import msgspec


@dataclass
class Status:
    # TODO: or int?
    stroke_mm: float
    adc: int
    auto: bool
    target_mm: float | None = None


class Flower:
    class _Endpoints(StrEnum):
        status = "/status"
        move = "/move"
        stop = "/stop"

    def __init__(self, endpoint: str) -> None:
        # TODO: Error handle the endpoint not containing http?
        self._endpoint: str = endpoint

    def _http_get(self, path: str, params: dict[str, str] | None = None) -> Response:
        resp = httpx.get(f"{self._endpoint}{path}", params=params).raise_for_status()
        return resp

    @staticmethod
    def _decode(content: bytes) -> Status:
        return msgspec.json.decode(content, type=Status, strict=False)

    def status(self) -> Status:
        content = self._http_get(self._Endpoints.status).content
        return self._decode(content)

    def move(self, pos: int) -> Status:
        content = self._http_get(self._Endpoints.move, {"band": str(pos)}).content
        return self._decode(content)

    def stop(self) -> Status:
        content = self._http_get(self._Endpoints.stop).content
        return self._decode(content)
