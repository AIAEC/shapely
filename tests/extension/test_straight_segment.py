from copy import deepcopy
from unittest import TestCase

from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.geometry import Point


class StraightSegmentTest(TestCase):
    def test_create(self):
        with self.assertRaises(ValueError):
            StraightSegment([(0, 0), (1, 1), (2, 2)])

        line0 = StraightSegment()
        self.assertTrue(line0.is_empty)

        line1 = StraightSegment([(0, 0), (0, 0)])
        self.assertFalse(line1.is_empty)

        line2 = StraightSegment([(0, 0), (0, 1)])
        self.assertTrue(line2.length == 1)

        line3 = deepcopy(line2)
        self.assertEqual(line2, line3)

    def test_point_on_left(self):
        line = StraightSegment([(0, 0), (1, 0)])
        self.assertTrue(line.point_on_left(Point(0, 0.5)))
        self.assertFalse(line.point_on_left(Point(0, -0.5)))

    def test_point_on_right(self):
        line = StraightSegment([(0, 0), (1, 0)])
        self.assertTrue(line.point_on_right(Point(0, -0.5)))
        self.assertFalse(line.point_on_right(Point(0, 0.5)))

    def test_point_on_line(self):
        line = StraightSegment([(0, 0), (1, 0)])
        self.assertTrue(line.point_on_line(Point(0.5, 0)))
        self.assertFalse(line.point_on_line(Point(0, 0.5)))
