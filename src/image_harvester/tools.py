from image_harvester.config import FLOWER_CONFIG_PATH, Config


def cli_ping() -> None:
    config = Config.parse(FLOWER_CONFIG_PATH)
    ...
