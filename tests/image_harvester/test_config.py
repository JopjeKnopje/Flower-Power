from ipaddress import IPv4Address
import pathlib

from image_harvester.config import Config


def x() -> pathlib.Path | IPv4Address:
    return pathlib.Path("image-harvester.toml")


def test_read() -> None:

    data = """
    flower_endpoint = "192.168.0.42"
    recordings_output_dir = "test-recordings"

    [[cameras]]
    uri = "192.1"
    panorama_location = 1
    rstp_path = "/axis-media/media.amp"
    username = "root"
    password = "admin"


    [[cameras]]
    uri = "192.1"
    panorama_location = 2
    rstp_path = "/axis-media/media.amp"
    username = "root"
    password = "admin"
    """

    c = Config.parse(data)

    assert len(c.cameras) == 2

    assert c.flower_endpoint == "192.168.0.42"

    assert c.cameras[0].username == "root"
    assert c.cameras[0].password == "admin"

