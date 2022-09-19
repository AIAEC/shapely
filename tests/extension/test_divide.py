from math import sqrt
from operator import attrgetter
from unittest import TestCase

from shapely.extension.util.divide import _line_divided_by_points, _divide_polygon_by_multilinestring
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union


class DivideTest(TestCase):
    def test_line_divided_by_points(self):
        line = LineString([(0, 0), (10, 10)])
        points = [Point(5, 5), Point(7, 7.0000001)]
        segments = _line_divided_by_points(line, points, dist_tol=0.001)
        self.assertEqual(3, len(segments))
        segments.sort(key=attrgetter('length'))
        self.assertAlmostEqual(2 * sqrt(2), segments[0].length, delta=1e-3)
        self.assertAlmostEqual(3 * sqrt(2), segments[1].length, delta=1e-3)
        self.assertAlmostEqual(5 * sqrt(2), segments[2].length, delta=1e-3)

    def test_divide_polygon_by_multilinestring(self):
        poly = box(0, 0, 10, 10)
        line0 = LineString([(5, 0), (5, 10)])
        line1 = LineString([(-1, 5), (6, 5)])
        result = _divide_polygon_by_multilinestring(poly, unary_union([line0, line1]))
        self.assertTrue(result)