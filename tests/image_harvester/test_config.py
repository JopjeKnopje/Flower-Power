from dataclasses import dataclass
from ipaddress import IPv4Address
import os
import pathlib
import tempfile
import pytest
from pytest import MonkeyPatch

from image_harvester.config import Camera, Config
from image_harvester.video import (
    VideoSource,
    VideoSourceRTP,
    VideoSourceURI,
    VideoStream,
)


def x() -> pathlib.Path | IPv4Address:
    return pathlib.Path("image-harvester.toml")


@pytest.fixture
def config_data() -> str:
    data = """
    flower_endpoint = "192.168.0.42"

    [[cameras]]
    uri = "192.168.0.4"
    rstp_path = "/axis-media/media.amp"
    username = "root"
    password = "admin"


    [[cameras]]
    uri = "192.168.0.200"
    rstp_path = "/axis-media/media.amp"
    username = "root"
    password = "admin"
    """
    return data


def test_read_data(config_data: str) -> None:

    c = Config.parse(config_data)

    assert len(c.cameras) == 2

    assert c.flower_endpoint == "192.168.0.42"

    assert c.cameras[0].username == "root"
    assert c.cameras[0].password == "admin"

    assert str(c.cameras[0].uri) == "192.168.0.4"


def test_read_file_not_found(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("FLOWER_CONFIG_PATH", "non-existent")

    with pytest.raises(FileNotFoundError):
        _ = Config.read()


def test_read_file(monkeypatch: MonkeyPatch, config_data: str) -> None:

    with tempfile.NamedTemporaryFile(delete=False) as f:
        _ = f.write(config_data.encode())

    monkeypatch.setenv("FLOWER_CONFIG_PATH", f.name)
    _ = Config.read()


def test_create_source_rtp() -> None:

    c = Camera("192.168.0.2")
    s = VideoSource.from_cfg_camera(c)
    assert isinstance(s, VideoSourceRTP)


def test_create_source_uri() -> None:

    filename = "text.txt"

    c = Camera(filename)
    s = VideoSource.from_cfg_camera(c)

    assert isinstance(s, VideoSourceURI)
    assert s.uri == f"{os.getcwd()}/{filename}"


# TODO: Add fixture which pings the camera, if the cameras are connected, return their addresses as a list
@pytest.mark.skip(reason="Camera may not be connected")
def test_create_streams() -> None:
    config = Config(
        flower_endpoint="192.168.0.42",
        cameras=[
            Camera("192.168.0.2"),
            Camera("192.168.0.3"),
            Camera("192.168.0.4"),
        ],
    )

    streams: list[VideoStream] = []

    for c in config.cameras:
        streams.append(VideoStream(VideoSource.from_cfg_camera(c)))



def test_dataclass_static() -> None:

    @dataclass
    class StorageData:
        value: int
        def __init__(self) -> None:
            self.value = 321

    @dataclass
    class StorageDataNoInit:
        value: int


    class StorageReg:
        value: int
        def __init__(self) -> None:
            self.value = 321

    sd = StorageData()
    assert sd.value == 321
    # assert StorageData.value == 123

    sdni = StorageDataNoInit(321)
    assert sdni.value == 321
    # assert StorageData.value == 123


    sr = StorageReg()
    assert sr.value == 321
    # assert StorageReg.value == 123

