from dataclasses import dataclass
from pathlib import Path
import pathlib
from typing import Self
import msgspec


@dataclass
class Camera:
    # TODO: Use `Path | IPv4Address` types for this
    uri: str
    # used for stitching together the resulting image
    panorama_location: int

    rstp_path: str | None
    username: str | None
    password: str | None


def dec_hook(type: type[Path], obj: str) -> Path:

    if type is Path:
        return pathlib.Path(str(obj))

    raise TypeError("Type not supported by hook")


@dataclass
class Config:
    cameras: list[Camera]
    flower_endpoint: str
    recordings_output_dir: Path | None

    @classmethod
    def read(cls, file: Path) -> Self:
        with open(file, "r") as f:
            return cls.parse(f.read())

    @classmethod
    def parse(cls, data: str) -> Self:
        return msgspec.toml.decode(data, dec_hook=dec_hook, type=cls)

