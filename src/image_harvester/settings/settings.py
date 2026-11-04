from abc import ABC
from os import environ
from pathlib import Path


def env_to_bool(name: str, default: bool) -> bool:
    val = environ.get(name, str(default))
    return val.lower() in ["true", "yes"]


class Settings(ABC):
    _debug: bool = True
    server_host: str = "0.0.0.0"
    server_port: int = 5000
    headless: bool = env_to_bool("IH_HEADLESS", True)
    yolo_device: str = environ.get("IH_YOLO_DEV", "cpu")
    crop_save_dir: Path = Path("crop-settings")

    @property
    def debug(self) -> bool:
        return self._debug


class SettingsDev(Settings): ...


class SettingsPytest(SettingsDev): ...


class SettingsProd(Settings): ...
