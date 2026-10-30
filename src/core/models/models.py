from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

zone = ZoneInfo("Europe/Amsterdam")


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
