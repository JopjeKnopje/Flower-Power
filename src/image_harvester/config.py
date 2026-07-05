from dataclasses import dataclass
from ipaddress import AddressValueError, IPv4Address
import os
from pathlib import Path
import pathlib
from typing import Self
import msgspec


FLOWER_CONFIG_PATH = "image-harvester.toml"


# TODO: Think about video recording location
@dataclass
class Camera:
    # TODO: Currently msgspec doens't support using `Path | IPv4Address` for this.
    uri: str | int

    rstp_path: str = "/axis-media/media.amp"
    username: str = "root"
    password: str = "admin"

    # dirty trick, we just parse at runtime
    def get_uri(self) -> Path | IPv4Address | int:
        if isinstance(self.uri, int):
            return self.uri
        try:
            return IPv4Address(self.uri)
        except AddressValueError:
            return pathlib.Path(self.uri)


def dec_hook(type: type[Path], obj: str) -> Path:

    if type is Path:
        return pathlib.Path(str(obj))

    raise TypeError("Type not supported by hook")


# NOTE: Make this static?
@dataclass
class Config:
    cameras: list[Camera]
    flower_endpoint: str
    yolo_verbose: bool = True
    flower_interval: int = 3
    recording_dir: str | None = None

    @classmethod
    def read(cls, file: Path | None = None) -> Self:
        if file is None:
            file = pathlib.Path(os.getenv("FLOWER_CONFIG_PATH", FLOWER_CONFIG_PATH))
        with open(file, "r") as f:
            return cls.parse(f.read())

    @classmethod
    def parse(cls, data: str) -> Self:
        return msgspec.toml.decode(data, dec_hook=dec_hook, type=cls)
