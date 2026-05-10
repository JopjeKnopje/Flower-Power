from math import dist
import time




def step(time: float) -> None:

    # meter/second
    vel = 0.10
    # meter
    cylinder_length = 1.0
    print(f"time: {time}ms")

    distance = (vel * (time / 1000)) % cylinder_length


    print(f"position: m {distance:.5f}")


def time_millis() -> int:
    return round(time.time() * 1000)

def main() -> None:
    time_zero = time_millis()
    while True:
        # TODO: Take delta time instead to fix drift
        step(time_millis() - time_zero)
        time.sleep(0.1)




