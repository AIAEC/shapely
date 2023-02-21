from math import sqrt
from operator import attrgetter
from unittest import TestCase

from shapely.extension.util.divide import _line_divided_by_points, _divide_polygon_by_multilinestring, divide
from shapely.geometry import LineString, Point, box, Polygon
from shapely.ops import unary_union
from shapely.wkt import loads


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
        self.assertEqual(3, len(result))

    def test_divide_by_non_linestring(self):
        poly = box(0, 0, 10, 10)
        slice_ = box(5, -1, 6, 11)
        result = divide(poly, slice_)
        self.assertEqual(2, len(result))
        self.assertTrue(all(isinstance(item, Polygon) for item in result))

    def test_divide_by_linestring(self):
        poly = box(0, 0, 10, 10)
        line = LineString([(0, 0), (0, 10)])
        result = divide(poly, line)
        self.assertEqual(1, len(result))
        self.assertTrue(poly.equals(result[0]))

        line = LineString([(5, 0), (5, 10)])
        result = divide(poly, line)
        self.assertEqual(2, len(result))
        self.assertTrue(all(isinstance(item, Polygon) for item in result))

        line = LineString([(5, -1), (5, 5)])
        result = divide(poly, line)
        self.assertEqual(1, len(result))
        self.assertTrue(isinstance(result[0], Polygon))

    def test_divide_by_boundary(self):
        poly = box(0, 0, 1, 1)
        line = LineString([(0, 0), (1, 0)])
        result = divide(poly, line)
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].equals(poly))

        line = LineString([(0, 0), (1, 0), (1, 1)])
        result = divide(poly, line)
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].equals(poly))

    def test_divided_by_grid(self):
        poly = box(0, 0, 10, 10)
        multi_line = loads('MULTILINESTRING ((0 7, 10 7),(0 5, 10 5),(5 0, 5 10))')
        result = divide(poly, multi_line)
        self.assertEqual(6, len(result))

        multi_line = loads('MULTILINESTRING ((0 7, 10 7),(0 5, 10 5),(5 0, 5 8))')
        result = divide(poly, multi_line)
        result = sorted(result, key=lambda p: p.area, reverse=True)
        self.assertEqual(5, len(result))
        self.assertEqual(6, len(result[0].exterior.ext.decompose(Point).to_list()))

        multi_line = loads('MULTILINESTRING ((5 0, 5 5),(5 5, 8 5),(8 5, 8 8))')
        result = divide(poly, multi_line)
        self.assertEqual(1, len(result))
