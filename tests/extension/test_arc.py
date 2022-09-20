from math import pi
from unittest import TestCase

from shapely.extension.geometry.arc import Arc
from shapely.geometry import Point


class ArcTest(TestCase):
    def test_arc(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=90, resolution=3)
        self.assertAlmostEqual(pi / 2, arc.length)
        self.assertTrue(arc.centroid.equals(Point(0, 0)))
        self.assertTrue(arc.is_ccw)
        self.assertTrue(arc.reverse.is_cw)
        self.assertEqual(90, arc.angle)
        self.assertTrue(arc.is_minor_arc)
        self.assertFalse(arc.is_prior_arc)
        self.assertFalse(arc.is_half_circle)
        self.assertTrue(arc.interpolate(0).equals(Point(1, 0)))

    def test_complementary_arc(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=91, resolution=3).complementary
        self.assertAlmostEqual((360 - 91) * pi / 180, arc.length)
        self.assertTrue(arc.centroid.equals(Point(0, 0)))
        self.assertFalse(arc.is_cw)
        self.assertEqual(360 - 91, arc.angle)
        self.assertFalse(arc.is_minor_arc)
        self.assertTrue(arc.is_prior_arc)
        self.assertFalse(arc.is_half_circle)

    def test_minor_arc_and_prior_arc(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=91, resolution=3)
        complementary_arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=91, resolution=3).complementary
        self.assertTrue(arc.get_minor_arc() is arc)
        self.assertTrue(complementary_arc.get_prior_arc() is complementary_arc)

        self.assertTrue(arc.get_prior_arc() == complementary_arc)
        self.assertAlmostEqual(complementary_arc.get_minor_arc().length, arc.length)

    def test_interpolate_by_angle(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=180)
        self.assertTrue(arc.interpolate_by_angle(90).almost_equals(Point(0, 1)))
