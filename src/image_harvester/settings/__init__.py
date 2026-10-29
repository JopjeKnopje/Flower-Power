import os
import sys
from typing import Literal

from image_harvester.settings.settings import (
    Settings,
    SettingsDev,
    SettingsProd,
    SettingsPytest,
)

type Environment = Literal["dev", "prod"]


def load_settings() -> Settings:
    env_name = os.environ.get("IH_ENVIRONMENT", "dev").lower()

    # if we're running as pytest
    if "pytest" in sys.modules:
        return SettingsPytest()
    match env_name:
        case "dev":
            return SettingsDev()
        case "prod":
            return SettingsProd()
        case _:
            raise KeyError(f"{env_name} not a valid Environment")


# Super janky, but atleast gives some indication
def print_config(settings: Settings) -> None:
    print(f"loaded {type(settings).__name__}")
    for key in dir(settings):
        if not key.startswith("__"):
            val = getattr(settings, key)  # pyright: ignore[reportAny]
            print(f"{key} : {val}")


settings = load_settings()
print_config(settings)
