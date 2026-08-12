from dataclasses import dataclass
from pathlib import Path
from typing import final


@final
@dataclass
class Settings:
    CROP_SAVE_DIR = Path("crop-settings")
