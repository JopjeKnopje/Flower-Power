from queue import LifoQueue

data_queue: LifoQueue[int] = LifoQueue()


def get_queue() -> LifoQueue[int]:
    return data_queue
