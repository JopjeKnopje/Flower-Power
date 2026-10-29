import logging
from typing import final, override


def logger_init() -> logging.Logger:
    logger = logging.getLogger("image-harvester")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)
    return logger


@final
# TODO: Add `success` which is green
class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    reset = "\x1b[0m"
    format_str = "[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s] %(message)s"
    format_debug_str = "[%(asctime)s][%(filename)s:%(lineno)d][%(funcName)s][%(levelname)s] %(message)s"

    FORMATS: dict[int, str] = {
        logging.DEBUG: grey + format_debug_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: red + format_str + reset,
    }

    @override
    def format(self, record: logging.LogRecord):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)
