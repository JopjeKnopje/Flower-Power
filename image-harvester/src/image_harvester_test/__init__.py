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
    color: Scalar = Color.WHITE

    @abstractmethod
    def draw(self, frame: MatLike) -> None:
        pass

class Point(Shape):
    @override
    def draw(self, frame: MatLike) -> None:
        x = self.p1[0]
        y = self.p1[1]
        thickness = 5
        _ = cv2.rectangle(frame, (x, y), (x + thickness, y + thickness), self.color, -1)


class Line(Shape):
    p2: Vec2i

    def __init__(self, position: Vec2i, end: Vec2i, color: Scalar=Shape.color) -> None:
        Shape.__init__(self, position, color)
        self.p2 = end


    @override
    def draw(self, frame: MatLike) -> None:
        start_x = self.p1[0]
        start_y = self.p1[1]
        end_x = self.p2[0]
        end_y = self.p2[1]

        _ = cv2.line(frame, (start_x, start_y), (end_x, end_y), self.color, 1)



# https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#Line_defined_by_two_points
def find_distance(p: Point, line: Line) -> float:
    numerator  = abs(
        (line.p1[1] - line.p2[1]) * p.p1[0]
        -
        (line.p1[0] - line.p2[0]) * p.p1[1]
        + 
        (line.p2[0] * line.p1[1]) -  (line.p2[1] * line.p1[0])
    )
    denominator = sqrt((line.p1[0] - line.p2[0])**2 - (line.p1[1] - line.p2[1])**2)

    return numerator / denominator

def find_line(p: Point, line: Line) -> Line:
    # 1. calculate slope of `line` called `m`
    m  = (line.p1[1] - line.p2[1]) / (line.p1[0] - line.p2[0])
    # 2. get angle of slope and rotate 90 degrees it its perpendicular to `line`
    # TODO: Remove this step and use `m` directly
    l_angle = atan(m) + radians(90)
    # 3. construct new equation for us to draw a new line with intersecting `line`
    m_new = degrees(tan(l_angle))




def main() -> None:
    frame = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), np.uint8)
    points: list[Shape] = [
        Point([*point_location]),
        Point([25, 25]),
        Line([52, 81], [138, 100])
    ]



    for p in points:
        p.draw(frame)


    distance = find_distance(points[0], points[2])

    find_line(points[0], points[2])
    # Line(points[0], line_intersect)
    print(f"distance {distance}")



    cv2.imshow("test", frame)
    _ = cv2.waitKey(0)


    cv2.destroyAllWindows()
