from image_harvester.cropper import Cropper


MAX_LEN = 3


def cycle_next(x: int, dir: int = 1) -> int:
    return Cropper._cycle_stream(x, dir, MAX_LEN)  # pyright: ignore[reportPrivateUsage]


def test_cycle() -> None:

    x = 0

    x = cycle_next(x, 1)
    assert x == 1

    x = cycle_next(x, 1)
    assert x == 2

    x = cycle_next(x, 1)
    assert x == 0

    x = cycle_next(x, 1)
    assert x == 1

    x = cycle_next(x, 1)
    assert x == 2

    x = cycle_next(x, -1)
    assert x == 1

    x = cycle_next(x, -1)
    assert x == 0

    x = cycle_next(x, -1)
    assert x == 2
