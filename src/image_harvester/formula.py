import matplotlib.pyplot as plt
import numpy as np


def formula() -> None:
    fig, ax = plt.subplots()

    t = np.arange(0.0, 3.0, 0.01)
    data = np.atan(2 * np.pi * t) / 1.5

    ax.plot(t, data)

    ax.grid()
    plt.show()
