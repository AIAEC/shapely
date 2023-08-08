from math import isclose

from shapely.extension.constant import MATH_LARGE_EPS
from shapely.extension.model.coord import Coord
from shapely.geometry import Point


def test_three_points_angle():
    coord0, coord1, coord2 = (0, 0), (10, 0), (10, 10)
    pt0, pt1, pt2 = Point(coord0), Point(coord1), Point(coord2)
    angle0 = Coord.three_points_angle(pt0, pt1, pt2)
    assert isclose(angle0.degree, 90, abs_tol=MATH_LARGE_EPS)

    angle1 = Coord.three_points_angle(coord2, coord1, coord0)
    assert isclose(angle0 - angle1, 0, abs_tol=MATH_LARGE_EPS)

    angle2 = Coord.including_angles([coord2, coord1, coord0])[0]
    assert not isclose(angle0.degree - angle2.degree, 0, abs_tol=MATH_LARGE_EPS)

    angle3 = Coord.including_angles([coord0, coord1, coord2])[0]
    assert isclose(angle0 - angle3, 0, abs_tol=MATH_LARGE_EPS)


