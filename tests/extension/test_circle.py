from math import pi
from unittest import TestCase

from shapely.extension.geometry.circle import Circle
from shapely.geometry import LineString


class CircleTest(TestCase):
    def test_intersects(self):
        circle = Circle((0, 0), 1, resolution=1)
        self.assertTrue(circle.intersects(LineString([(0, 0.99999), (1, 0.99999)])))

    def test_length(self):
        circle = Circle((0, 0), 1, resolution=1)
        self.assertAlmostEqual(2 * pi, circle.length)
