import httpx
import msgspec
from httpx import Response

from core.models.models import BoxesModel


class ImageHarvesterAPI:
    def __init__(self, host: str) -> None:
        self._host: str = host

    def _http_get(self) -> Response:
        endpoint = "/"
        resp = httpx.get(f"{self._host}{endpoint}").raise_for_status()
        return resp

    def get_boxes(self) -> list[BoxesModel]:
        content = self._http_get().content
        return self._decode(content)

    @staticmethod
    def _decode(content: bytes) -> list[BoxesModel]:
        return msgspec.json.decode(content, type=list[BoxesModel], strict=False)
