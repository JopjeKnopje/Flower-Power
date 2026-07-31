import pickle

import matplotlib.pyplot as plt

from image_harvester.smoothing import ema, sma


def plotter() -> None:

    data: list[int]
    with open("office_people.raw", "rb") as f:
        data = pickle.load(f)  # pyright: ignore[reportAny]

    ema_data = ema(data, 0.05)
    sma_data = sma(data, 100)

    _ = plt.plot(data, color="black")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.plot(ema_data, color="red")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.plot(sma_data, color="blue")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.ylabel("values")  # pyright: ignore[reportUnknownMemberType]
    _ = plt.show()  # pyright: ignore[reportUnknownMemberType]
