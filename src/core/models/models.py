from abc import ABC
from dataclasses import dataclass


@dataclass
class BaseModel(ABC):
    """
    Base model for all flower data
    """


@dataclass
class TestModel(BaseModel):
    """
    Model for the TestProcessor
    """

    value: int
