from image_harvester.cropper import CropSelector


MAX_LEN = 3


def test_update_cs_simple() -> None:

    cs = CropSelector()

    assert cs.settings.start == (0, 0)
    assert cs.settings.end == (0, 0)

    cs._update_settings(end=(200, 200))  # pyright: ignore[reportPrivateUsage]
    assert cs.settings.end == (200, 200)
    assert cs.settings.start == (0, 0)

    cs._update_settings(start=(100, 100))  # pyright: ignore[reportPrivateUsage]
    assert cs.settings.start == (100, 100)

    cs._update_settings(start=(300, 300))  # pyright: ignore[reportPrivateUsage]
    assert cs.settings.end == (300, 300)
