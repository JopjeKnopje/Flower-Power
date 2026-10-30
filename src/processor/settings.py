from dataclasses import dataclass
from pathlib import Path
from typing import final

type Vec4f = tuple[float, float, float, float]


@final
@dataclass
class Settings:
    CROP_SAVE_DIR = Path("crop-settings")
