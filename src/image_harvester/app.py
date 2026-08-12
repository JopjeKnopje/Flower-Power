import platform
import sys


from image_harvester.logs import logger_init

logger = logger_init()


def host_is_headless() -> bool:
    # check if we're running on the RPI
    return sys.platform == "linux" and platform.machine() == "aarch64"
