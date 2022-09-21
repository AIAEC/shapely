from math import pi
from unittest import TestCase

from shapely.extension.geometry.circle import Circle
from shapely.geometry import LineString, Point


class CircleTest(TestCase):
    def test_intersects(self):
        circle = Circle((0, 0), 1, resolution=1)
        self.assertTrue(circle.intersects(LineString([(0, 0.99999), (1, 0.99999)])))

    def test_length(self):
        circle = Circle((0, 0), 1, resolution=1)
        self.assertAlmostEqual(2 * pi, circle.length)

    def test_concentric(self):
        circle = Circle((0, 0), 1, resolution=1)
        self.assertTrue(circle.concentric(2).almost_equals(Circle((0, 0), 2, resolution=1)))

    def test_arc(self):
        circle = Circle((0, 0), 10, resolution=1)
        arcs = circle.arc(Point(9, 0))
        self.assertEqual(1, len(arcs))

        arcs = circle.arc([Point(9, 0), Point(0, 1)])
        self.assertEqual(2, len(arcs))
        arcs.sort(key=lambda arc: arc.length)
        self.assertAlmostEqual(10 * 2 * pi / 4, arcs[0].length)
        self.assertAlmostEqual(10 * 2 * pi * 3 / 4, arcs[1].length)

        arcs = circle.arc([Point(4, 4), Point(4, -4)])
        self.assertEqual(2, len(arcs))
        arcs.sort(key=lambda arc: arc.length)
        self.assertAlmostEqual(10 * 2 * pi / 4, arcs[0].length)
        self.assertAlmostEqual(10 * 2 * pi * 3 / 4, arcs[1].length)
