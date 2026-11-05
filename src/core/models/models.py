from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Self
from zoneinfo import ZoneInfo

import msgspec

# TODO: Use a proper class for it, for better readablilty
type Vec4f = tuple[float, float, float, float]


# @dataclass
# class Position:
#     x: float
#     y: float
#
# @dataclass
# class Dimensions:
#     width: float
#     height: float
#
# @dataclass
# class Box:
#     pos: Position
#     dimension: Dimensions
#
@dataclass
class BaseModel(ABC):
    """
    Base model for all flower data
    """

    timestamp: float = field(
        default_factory=lambda: datetime.now(
            tz=ZoneInfo("Europe/Amsterdam")
        ).timestamp()
    )

    @classmethod
    def parse(cls, data: str) -> Self:
        return msgspec.json.decode(data, type=cls)


@dataclass
class BoxesModel(BaseModel):
    """
    The Harvester can detect multiple Boxes per frame, a box is simply a 4 point vector.
    We can also have an empty frame, which we represent as None.
    """

    boxes: list[Vec4f] | None = None
