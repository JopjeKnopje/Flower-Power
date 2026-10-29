import subprocess
from ipaddress import IPv4Address
from typing import Callable

from image_harvester.flower_config import FlowerConfig
from image_harvester.logs import logger_init

logger = logger_init()


ArgvTuple = tuple[str, ...]


def _ping_command(addr: IPv4Address) -> ArgvTuple:
    return ("ping", "-c1", str(addr))


def _get_commmands(config: FlowerConfig) -> list[ArgvTuple]:
    commands: list[ArgvTuple] = []
    for c in config.cameras:
        uri = c.get_uri()
        if type(uri) is IPv4Address:
            commands.append(_ping_command(uri))
            logger.info(f"pinging {uri}")
    return commands


def _log_bytes(data: bytes, logging_func: Callable[[str], None]) -> None:
    lines = [s for s in data.decode().splitlines() if s.strip()]
    for line in lines:
        logging_func(line)


def ping() -> None:
    config = FlowerConfig.read()
    commands = _get_commmands(config)

    remotes = len(commands)
    online_cams = [False] * remotes

    while True:
        procs = [
            subprocess.Popen(i, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            for i in commands
        ]

        for i, p in enumerate(procs):
            try:
                stdout, _ = p.communicate(timeout=0.5)
                exit_code = p.returncode
            except subprocess.TimeoutExpired:
                continue
            if online_cams[i]:
                continue

            if exit_code == 0:
                online_cams[i] = True
                logger.info(f"{config.cameras[i].get_uri()} online")
                remotes -= 1
            else:
                _log_bytes(stdout, logger.warning)

        if sum(online_cams) == len(commands):
            logger.info("online")
            break
