from ipaddress import IPv4Address
import os
import pathlib
import tempfile
import pytest
from pytest import MonkeyPatch

from image_harvester.config import Camera, Config
from image_harvester.harvester import VideoSource, VideoSourceRTP, VideoSourceURI


def x() -> pathlib.Path | IPv4Address:
    return pathlib.Path("image-harvester.toml")


@pytest.fixture
def config_data() -> str:
    data = """
    flower_endpoint = "192.168.0.42"
    recordings_output_dir = "test-recordings"

    [[cameras]]
    uri = "192.168.0.4"
    panorama_location = 1
    rstp_path = "/axis-media/media.amp"
    username = "root"
    password = "admin"


    [[cameras]]
    uri = "192.168.0.200"
    panorama_location = 2
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


def test_read_data_defaults_not_set() -> None:
    data = """
    flower_endpoint = "192.168.0.42"
    recordings_output_dir = "test-recordings"

    [[cameras]]
    uri = "192.168.0.4"
    panorama_location = 1
    rstp_path = "/axis-media/media.amp"
    password = "admin"
    """

    c = Config.parse(data)
    # check that default value is applied correctly
    assert c.cameras[0].username is Camera.username


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

    c = Camera("192.168.0.2", 1)
    s = VideoSource(c)
    assert isinstance(s, VideoSourceRTP)


def test_create_source_uri() -> None:

    filename = "text.txt"

    c = Camera(filename, 1)
    s = VideoSource(c)

    assert isinstance(s, VideoSourceURI)
    assert s == f"{os.getcwd()}/{filename}"
