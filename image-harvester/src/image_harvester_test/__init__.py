from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import EnumDict
from re import S
from typing import override
from math import sqrt, atan, tan, radians, degrees

import cv2
import numpy as np
from cv2.typing import (
    MatLike,
    Scalar,
    Vec2i,
)

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

point_location = (500, 500)

class Color(EnumDict):
    WHITE: Scalar = (255,255,255)

@dataclass
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
        _ = cv2.rectangle(frame, (x, y), (x + thickness, y + thickness), self._color, -1)


class Line(Shape):
    p2: Vec2i

    def __init__(self, position: Vec2i, end: Vec2i, color: Scalar=Shape._color) -> None:
        Shape.__init__(self, position, color)
        self.p2 = end

   


    @override
    def draw(self, frame: MatLike) -> None:
        start_x = self.p1[0]
        start_y = self.p1[1]
        end_x = self.p2[0]
        end_y = self.p2[1]

        _ = cv2.line(frame, (start_x, start_y), (end_x, end_y), self._color, 1)


def point_to_point_dist(p1: Point, p2: Point) -> float:
    return sqrt(abs((p1.p1[0] - p2.p1[0])**2 + (p1.p1[1] - p2.p1[1])**2))


# TODO : Understand this stuff
# https://stackoverflow.com/a/1501725/7363348
# https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#A_vector_projection_proof
def find_line(p: Point, line: Line) -> Line:

    line_squared = (line.p1[0] - line.p2[0])**2 + (line.p1[1] - line.p2[1])**2
    if (line_squared == 0.0):
        # TODO: See when this gets triggered
        return Line(p.p1, line.p1)
    dot_product = (
        (p.p1[0] - line.p1[0]) * (line.p2[0] - line.p1[0]) +
        (p.p1[1] - line.p1[1]) * (line.p2[1] - line.p1[1])
        )
    t = max(0, min(1, dot_product / line_squared))
    vec = (
        int(line.p1[0] + t * (line.p2[0] - line.p1[0])),
        int(line.p1[1] + t * (line.p2[1] - line.p1[1]))
    )

    proj = Point(vec)
    dist = point_to_point_dist(p, proj)

    print(f"t: {proj}")
    print(f" p: {p.p1} | proj {proj.p1} | distance: {dist}")
    return Line(p.p1, proj.p1)



def main() -> None:
    frame = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), np.uint8)
    points: list[Shape] = [
        Point([100, 100]),
        Line([5, 50], [50, 5])
    ]


    for p in points:
        p.draw(frame)


    # TODO: Fix polymorhpism
    l = find_line(points[0], points[1])
    l.set_color(0xff1111)
    l.draw(frame)
    # Line(points[0], line_intersect)
    # print(f"distance {distance}")



    cv2.imshow("test", frame)
    _ = cv2.waitKey(0)


    cv2.destroyAllWindows()
