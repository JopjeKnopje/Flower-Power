import pytest


from image_harvester.flower_api import Flower


@pytest.fixture
def api() -> Flower:
    return Flower("http://192.168.0.42")


def test_enable_main_mode(api: Flower) -> None:

    m = api.main_mode(True)
    assert m == ""


def test_disable_main_mode(api: Flower) -> None:

    m = api.main_mode(False)
    assert m == ""
