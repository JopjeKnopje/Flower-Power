import matplotlib.pyplot as plt
import numpy as np


def formula() -> None:
    fig, ax = plt.subplots()

    t = np.arange(0.0, 1.0, 0.01)
    data_f1 = np.atan(2 * 2 * np.pi * t) / 1.5

    ax.plot(t, data_f1)

    t = np.arange(0.0, 1.0, 0.01)
    data_f2 = 1 + 2**t * -1

    ax.plot(t, data_f2)

    print(f"\n\nvalue {data_f2}")

    ax.grid()
    plt.show()
