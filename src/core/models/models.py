from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

zone = ZoneInfo("Europe/Amsterdam")
type Vec4f = tuple[float, float, float, float]


@dataclass
class BaseModel(ABC):
    """
    Base model for all flower data
    """

    timestamp: float = field(default_factory=lambda: datetime.now(tz=zone).timestamp())


@dataclass
class TestModel(BaseModel):
    """
    Model for the TestProcessor
    """

    value: int = 0


@dataclass
class Box:
    y_start: int
    y_end: int
    x_start: int
    x_end: int

    @property
    def width(self) -> int:
        return abs(self.x_end - self.x_start)

    @property
    def heigth(self) -> int:
        return abs(self.y_end - self.y_start)


@dataclass
class BoxesModel(BaseModel):
    """
    Model for the TestProcessor
    """

    # boxes: list[Box]
