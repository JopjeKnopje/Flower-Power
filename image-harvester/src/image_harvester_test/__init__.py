from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import EnumDict
from re import S
from typing import override

import cv2
import numpy as np
from cv2.typing import (
    MatLike,
    Scalar,
    Vec2i,
)

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

point_location = (50, WINDOW_HEIGHT - 50)

class Color(EnumDict):
    WHITE: Scalar = (255,255,255)

@dataclass
class Shape(ABC):
    position: Vec2i
    color: Scalar = Color.WHITE

    @abstractmethod
    def draw(self, frame: MatLike) -> None:
        pass

class Point(Shape):
    @override
    def draw(self, frame: MatLike) -> None:
        x = self.position[0]
        y = self.position[1]
        thickness = 5
        _ = cv2.rectangle(frame, (x, y), (x + thickness, y + thickness), self.color, -1)


class Line(Shape):
    end: Vec2i

    def __init__(self, position: Vec2i, end: Vec2i, color: Scalar=Shape.color) -> None:
        Shape.__init__(self, position, color)
        self.end = end


    @override
    def draw(self, frame: MatLike) -> None:
        start_x = self.position[0]
        start_y = self.position[1]
        end_x = self.end[0]
        end_y = self.end[1]

        _ = cv2.line(frame, (start_x, start_y), (end_x, end_y), self.color, 1)


def main() -> None:
    frame = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), np.uint8)
    points: list[Shape] = [
        Point([*point_location]),
        Point([25, 25]),
        Line([25, 25], [100, 100])
    ]




    for p in points:
        p.draw(frame)



    cv2.imshow("test", frame)
    _ = cv2.waitKey(0)


    cv2.destroyAllWindows()
