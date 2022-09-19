from unittest import TestCase

from shapely.geometry import Point, LineString


class LineStringExtension(TestCase):
    def test_projected_point(self):
        line = LineString([(0, 0), (1, 0)])
        result = line.ext.projected_point(Point(100, 1))
        self.assertTrue(result.equals(Point(100, 0)))
