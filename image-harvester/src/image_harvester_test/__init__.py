from math import sqrt
import cv2
import numpy as np

from shapes import Line, Point, Shape

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

point_location = (500, 500)


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
        Point([45, 120]),
        Line([50, 100], [100, 50]),
        Line([58, 150], [200, 50])
    ]


    # TODO: Fix polymorhpism
    l = find_line(points[0], points[2])
    l.set_color(0xff1111)
    l.draw(frame)

    l = find_line(points[1], points[2])
    l.set_color(0xff1111)
    l.draw(frame)
    # Line(points[0], line_intersect)
    # print(f"distance {distance}")


    for p in points:
        p.draw(frame)


    cv2.imshow("test", frame)
    _ = cv2.waitKey(0)


    cv2.destroyAllWindows()
