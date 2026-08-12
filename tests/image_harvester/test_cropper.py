import msgspec

from image_harvester.cropper import CropSelector


MAX_LEN = 3


def test_write_to_file() -> None:

    cs = CropSelector()

    cs.crop_start = (200, 100)
    cs.crop_end = (500, 700)

    dec = msgspec.json.Encoder()
    data = dec.encode(cs)
    assert data == ""
