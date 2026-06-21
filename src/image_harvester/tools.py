from ipaddress import IPv4Address
import subprocess

from image_harvester.config import Config
from image_harvester.logger import logger_init

logger = logger_init()


def ping_command(addr: IPv4Address) -> list[str]:
    return ["ping", "-c1", str(addr)]


def cli_ping() -> None:
    config = Config.read()
    commands: list[list[str]] = []

    for c in config.cameras:
        uri = c.get_uri()
        if type(uri) is IPv4Address:
            commands.append(ping_command(uri))
            logger.info(f"probing {uri}")
    while True:
        remotes = len(commands)
        procs = [
            subprocess.Popen(i, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            for i in commands
        ]
        for i, p in enumerate(procs):
            stdout, _ = p.communicate()
            exit_code = p.wait()
            if exit_code == 0:
                logger.info(f"{config.cameras[i].get_uri()} online")
                remotes -= 1
            else:
                lines = [s for s in stdout.decode().splitlines() if s.strip()]
                for line in lines:
                    logger.warning(line)

        if remotes == 0:
            print("all cameras online")
            break
