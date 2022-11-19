from math import sqrt
from unittest import TestCase

from shapely.extension.model.vector import Vector
from shapely.extension.util.shortest_path import ShortestStraightPath
from shapely.geometry import LineString, Polygon, box, MultiLineString, Point
from shapely.ops import nearest_points
from shapely.wkt import loads


class ShortestStraightPathTest(TestCase):
    def test_valid(self):
        polygon1 = loads("POLYGON ((240 300, 280 100, 790 80, 770 480, 480 430, 480 20, 240 300))")
        polygon2 = loads("POLYGON ((220 530, 650 530, 650 190, 220 190, 220 530))")
        result = ShortestStraightPath(Vector(1, 0)).of(polygon1, polygon2)
        self.assertTrue(result.is_empty)

    def test_intersection(self):
        line1 = loads("LINESTRING (220 510, 65 154, 520 300, 1120 250)")
        line2 = loads("LINESTRING (290 550, 430 70, 860 210, 740 410)")
        result = ShortestStraightPath(Vector(1, 0)).of(line1, line2)
        self.assertTrue(result.length == 0)

    def test_contain(self):
        polygon1 = loads("POLYGON ((250 470, 810 470, 810 110, 250 110, 250 470))")
        polygon2 = loads("POLYGON ((410 380, 660 380, 660 230, 410 230, 410 380))")
        result = ShortestStraightPath(Vector(1, 0)).of(polygon1, polygon2)
        self.assertTrue(result.length == 0 and polygon1.contains(result))

    def test_shortest_path(self):
        polygon1 = loads("POLYGON ((340 530, 658 435, 570 230, 564 238, 540 410, 500 190, 630 120, 600 60, 500 70,"
                         " 490 150, 420 60, 455 204, 461 213, 500 320, 360 200, 350 440, 500 390, 448 465, 290 490,"
                         " 340 530))")
        polygon2 = loads("POLYGON ((970 140, 980 154, 1150 180, 1130 270, 1120 420, 1080 470, 1040 280, 940 490, "
                         "790 330, 990 250, 810 70, 930 30, 970 140))")
        result = ShortestStraightPath().of(polygon1, polygon2)
        self.assertTrue(result.almost_equals(LineString(nearest_points(polygon1, polygon2))))

    def test_shortest_path_in_direction(self):
        polygon1 = Polygon(((0, 0), (0, 1), (1, 1), (1, 0)))
        polygon2 = Polygon(((4, 1), (5, 1), (5, 5), (3, 5)))
        line = LineString(((3, 5), (4, 1)))
        result1 = ShortestStraightPath(Vector(1, 1)).of(polygon1, polygon2)
        result2 = ShortestStraightPath(Vector(1, 1)).of(polygon1, line)
        correct_line = LineString(((1, 1), (3.4, 3.4)))
        self.assertTrue(result1.almost_equals(correct_line))
        self.assertTrue(result2.almost_equals(correct_line))

    def test_shortest_path_of_an_inner_line_to_boundary(self):
        box_ring = box(0, 0, 10, 10).exterior
        line = LineString([(5, -1), (5, 11)])

        path = ShortestStraightPath().of(box_ring, line)
        self.assertEqual(0, path.length)

        path = ShortestStraightPath(Vector(1, 0)).of(box_ring, line)
        self.assertEqual(0, path.length)

    def test_shortest_path_of_one_line_and_multilinestring(self):
        line = LineString([(1, 1), (2, 2)])

        multi_linestring = MultiLineString([
            LineString([(0, 0.5), (0.5, 0)]),
            LineString([(0, 10), (10, 0)])
        ])

        path = ShortestStraightPath(Vector(-1, -1)).of(line, multi_linestring)
        self.assertAlmostEqual(sqrt(2) * 3 / 4, path.length)

        path = ShortestStraightPath(Vector(1, 1)).of(line, multi_linestring)
        self.assertAlmostEqual(sqrt(2) * 3 / 4, path.length)

        path = ShortestStraightPath(Vector(1, 1)).of(line, multi_linestring, bidirect=False)
        self.assertAlmostEqual(10 / sqrt(2) - 2 * sqrt(2), path.length)

    def test_shortest_path_that_wont_be_valid(self):
        point = Point(0, 0)
        line = LineString([(0, -1), (-1, 0)])

        path = ShortestStraightPath(Vector(1, 1)).of(point, line, bidirect=False)
        self.assertEqual(0, path.length)

    def test_shortest_path_when_2_lines_intersect(self):
        line0 = LineString([(0, 1), (1, 0)])
        line1 = LineString([(0, 0), (1, 1)])

        path = ShortestStraightPath(Vector(1, 1)).of(line0, line1)
        self.assertEqual(0, path.length)

        path = ShortestStraightPath(Vector(1, 1)).of(line0, line1, bidirect=False)
        self.assertEqual(0, path.length)

        path = ShortestStraightPath(Vector(1, 1)).of(line1, line0, bidirect=False)
        self.assertEqual(0, path.length)

    def test_shortest_path_between_point_and_linestring(self):
        point = Point(0, 0)
        line = LineString([(0, 1), (1, 0)])
        path = ShortestStraightPath(Vector.from_endpoints_of(line).cw_perpendicular).of(point, line)
        self.assertTrue(path.almost_equals(LineString([(0, 0), (0.5, 0.5)])))

        path = ShortestStraightPath(Vector.from_endpoints_of(line).ccw_perpendicular).of(line, point)
        self.assertTrue(path.almost_equals(LineString([(0, 0), (0.5, 0.5)])))

        path = ShortestStraightPath(Vector.from_endpoints_of(line)).of(line, point)
        self.assertTrue(path.is_empty)

    def test_line_box_non_shortest_path(self):
        poly = box(0, 0, 1, 1)
        line = LineString([(10, 2), (10, 3)])
        result = ShortestStraightPath(Vector(1, 0)).of(poly, line)
        self.assertFalse(result)
        self.assertTrue(result.is_empty)
        self.assertEqual(0, result.length)

    def test_point_to_linear_ring_shortest_path(self):
        ring = Polygon([(0, 0), (10, 0), (10, 10)]).exterior
        point = Point(0, 5)
        path: LineString = ShortestStraightPath(Vector(-1, 0)).of(point, ring)
        self.assertTrue(path.ext.end().equals(Point(5, 5)))

        point = Point(0, 20)
        path: LineString = ShortestStraightPath(Vector(-1, 0)).of(point, ring)
        self.assertFalse(path)

    def test_empty_line_to_other_line_path(self):
        empty_line = LineString([(0 , 0), (0, 0)])
        line1 = LineString([(1, -1), (1, 1)])
        path = ShortestStraightPath(Vector(1, 0)).of(empty_line, line1)
        self.assertTrue(path)
        self.assertAlmostEqual(1, path.length)
        path = ShortestStraightPath(Vector(1, 0)).of(line1, empty_line)
        self.assertTrue(path)
        self.assertAlmostEqual(1, path.length)

        path = ShortestStraightPath(Vector(-1, 0)).of(empty_line, line1)
        self.assertTrue(path)
        self.assertAlmostEqual(1, path.length)
        path = ShortestStraightPath(Vector(-1, 0)).of(line1, empty_line)
        self.assertTrue(path)
        self.assertAlmostEqual(1, path.length)
