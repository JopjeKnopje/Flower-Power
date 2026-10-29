import pickle

import matplotlib.pyplot as plt

from image_harvester.smoothing import sma


def plotter() -> None:

    data_raw: list[int]
    with open("office_people.raw", "rb") as f:
        data_raw = pickle.load(f)  # pyright: ignore[reportAny]
    data_sma: list[float]
    with open("office_people.sma", "rb") as f:
        data_sma = pickle.load(f)  # pyright: ignore[reportAny]

    # ema_data = ema(data_raw, 0.05)
    data_sma_2 = sma(list(data_raw), 100)

    _ = plt.plot(data_raw, color="black")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.plot(data_sma, color="red")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.plot(data_sma_2, color="blue")  # pyright: ignore[reportUnknownMemberType]
    # _ = plt.plot(ema_data, color="red")  # pyright: ignore[reportUnknownMemberType]
    # _ = plt.plot(sma_data, color="blue")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.ylabel("values")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.show()  # pyright: ignore[reportUnknownMemberType]
