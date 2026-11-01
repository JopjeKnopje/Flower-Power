from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

type Vec4f = tuple[float, float, float, float]


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


@dataclass
class TestModel(BaseModel):
    """
    Model for the TestProcessor
    """

    value: int = 12


@dataclass
class BoxesModel(BaseModel):
    """
    The Harvester can detect multiple Boxes per frame, a box is simply a 4 point vector.
    We can also have an empty frame, which we represent as None.
    """

    box: list[Vec4f] | None = None
