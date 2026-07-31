from time import sleep

import httpx
import pytest

from image_harvester.flower_api import Flower


@pytest.fixture()
def flower_endpoint() -> str:
    # Get the already running flower mock. Or start our own in background. The already running flower mock should have a /reset endpoint, so we can keep it running.
    #
    # this should ideally start the mock in a background thread
    return "http://localhost:9000"


def test_status_initial(flower_endpoint: str) -> None:
    f = Flower(flower_endpoint)
    s = f.status()
    assert s.adc == 807
    assert s.stroke_mm == 0.0
    assert s.auto is False


def test_move_invalid(flower_endpoint: str) -> None:
    f = Flower(flower_endpoint)

    with pytest.raises(httpx.HTTPStatusError):
        _ = f.move(59)


def test_move_seq(flower_endpoint: str) -> None:
    f = Flower(flower_endpoint)

    target_mm = 50.0

    assert f.move(0).target_mm == target_mm
    while f.status().stroke_mm != target_mm:
        sleep(0.5)

    target_mm = 950
    assert f.move(9).target_mm == target_mm
    while f.status().stroke_mm != target_mm:
        sleep(0.5)

    assert f.stop()

    assert f.status().stroke_mm == target_mm


def test_move_seq_early_stop(flower_endpoint: str) -> None:
    f = Flower(flower_endpoint)

    target_mm = 50.0

    assert f.move(0).target_mm == target_mm
    while f.status().stroke_mm != target_mm:
        sleep(0.5)

    target_mm = 950
    assert f.move(9).target_mm == target_mm
    while f.status().stroke_mm < 400:
        sleep(0.5)

    pos = f.status().stroke_mm
    assert pos != 950 and pos != 50
