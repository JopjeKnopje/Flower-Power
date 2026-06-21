from ipaddress import IPv4Address

from image_harvester.tools import ping


def test_ping_unreachable() -> None:
    ip = "192.168.0.9"
    assert not ping(IPv4Address(ip))


def test_ping_reachable() -> None:
    ip = "0.0.0.0"
    assert ping(IPv4Address(ip))
