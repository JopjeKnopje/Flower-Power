from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import EnumDict
from typing import override

import cv2
from cv2.typing import (
    MatLike,
    Scalar,
    Vec2i,
)


# TODO: improve the way colors are done (maybe just support hex values?)
class Color(EnumDict):
    WHITE: Scalar = (255, 255, 255)
    BABY_BLUE: Scalar = (255, 150, 17)
    LIGHT_BLUE: Scalar = (255, 255, 17)
    RED: Scalar = (50, 50, 255)
    BLACK: Scalar = (0, 0, 0)


@dataclass()
class Shape(ABC):
    p1: Vec2i
    _color: Scalar = Color.WHITE

    @abstractmethod
    def draw(self, frame: MatLike) -> None:
        pass

    def set_color(self, color: Scalar) -> None:
        self._color = color


class Point(Shape):
    @override
    def draw(self, frame: MatLike) -> None:
        x = self.p1[0]
        y = self.p1[1]
        thickness = 5
        _ = cv2.rectangle(
            frame, (x, y), (x + thickness, y + thickness), self._color, -1
        )


class Line(Shape):
    p2: Vec2i

    def __init__(
        self, position: Vec2i, end: Vec2i, color: Scalar = Shape._color
    ) -> None:
        Shape.__init__(self, position, color)
        self.p2 = end

    @override
    def draw(self, frame: MatLike) -> None:
        start_x = self.p1[0]
        start_y = self.p1[1]
        end_x = self.p2[0]
        end_y = self.p2[1]

        _ = cv2.line(frame, (start_x, start_y), (end_x, end_y), self._color, 1)
