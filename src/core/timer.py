import time
from typing import final


@final
class Timer:
    def __init__(self) -> None:
        self.start()
        self._init = False

    @staticmethod
    def _time_func() -> float:
        return round(time.time() * 1000)

    def start_if_not_running(self) -> None:
        if not self._init:
            self.start()

    def start(self) -> None:
        self._init = True
        self._time_start = self._time_func()
        self._time_stop = 0

    def stop(self) -> None:
        self._time_stop = self._time_func()

    def delta(self) -> float:
        self.stop()
        return self._time_stop - self._time_start
