import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    _fig, ax = plt.subplots()

    t = np.arange(0.0, 1.0, 0.01)
    data_f1 = np.atan(2 * 2 * np.pi * t) / 1.5

    _ = ax.plot(t, data_f1)  # pyright: ignore[reportUnknownMemberType]

    t = np.arange(0.0, 1.0, 0.01)
    data_f2 = 1 + 2**t * -1

    _ = ax.plot(t, data_f2)  # pyright: ignore[reportUnknownMemberType]

    print(f"\n\nvalue {data_f2}")

    ax.grid()  # pyright: ignore[reportUnknownMemberType]
    plt.show()  # pyright: ignore[reportUnknownMemberType]
