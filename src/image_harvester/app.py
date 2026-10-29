import time

from image_harvester.queue import get_queue
from image_harvester.server.server import FlowerServer
from image_harvester.settings import config


def app() -> None:
    server = FlowerServer(host=config.server_host, port=config.server_port)

    with server.run_in_thread():
        print("Server is started.")
        value = 0
        while True:
            print("123")
            time.sleep(1)
            value += 1
            get_queue().put(value)

        # TODO: Pass generated data to queue.
