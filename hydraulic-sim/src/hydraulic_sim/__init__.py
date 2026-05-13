from math import dist
import time

step_freq = 100
step_sleep_time = (1 / 100)




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
    time_start = time_millis()

    while True:
        # TODO: Take delta time instead to fix drift
        time_current = time_millis()
        time_delta = time_current - time_start
        step(time_delta)
        time_zero = time_millis()
        time.sleep(step_sleep_time)




