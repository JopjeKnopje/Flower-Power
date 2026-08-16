from collections import deque
import pickle
import statistics

from image_harvester.smoothing import sma


# def test_sma() -> None:
#     with open("office_people.raw", "rb") as f:
#         data = pickle.load(f)  # pyright: ignore[reportAny]
#
#     sma_data = sma(data, 250)
#
#     assert sma_data == sma_data2
#
#
# def test_deque() -> None:
#     d: deque[int] = deque(maxlen=5)
#     d.append(1)
#     d.append(2)
#     d.append(3)
#     d.append(4)
#     d.append(5)
#
#     assert d is False
def test_list_smoothing() -> None:
    d: deque[int] = deque(maxlen=4)

    d.append(1)
    d.append(1)
    d.append(2)
    d.append(2)


    lst = list(d)
    assert int(statistics.mean(lst) + 0.5) == 1


