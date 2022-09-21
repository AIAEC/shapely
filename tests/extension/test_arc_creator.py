from math import isclose
from unittest import TestCase

from shapely.extension.constant import MATH_EPS
from shapely.extension.geometry import Circle
from shapely.extension.util.arc_creator import FixedRadiusArcCreator, FixedCenterArcCreator
from shapely.geometry import Point, LineString


class FixedRadiusCircleCreatorTest(TestCase):
    def test_create_circles_by_2_points(self):
        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(Point(10, 0))

        result = FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(Point(2, 0)).create_circles()
        self.assertEqual(1, len(result))
        self.assertTrue(Point(1, 0).almost_equals(result[0].centroid))
        self.assertAlmostEqual(1, result[0].radius)

        result = FixedRadiusArcCreator(1.5).intersects_with(Point(0, 0)).intersects_with(Point(2, 0)).create_circles()
        self.assertEqual(2, len(result))
        self.assertAlmostEqual(result[0].centroid.x, result[1].centroid.x)
        self.assertAlmostEqual(result[0].radius, result[1].radius)

    def test_create_circles_by_1_point_and_1_line(self):
        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(LineString([(-1, 10), (1, 10)]))

        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(LineString([(-1, 10), (1, 10)])).intersects_with(Point(0, 0))

        result = FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(
            LineString([(-1, 2), (1, 2)])).create_circles()
        self.assertEqual(1, len(result))
        self.assertTrue(Point(0, 1).almost_equals(result[0].centroid))
        self.assertAlmostEqual(1, result[0].radius)

        result = FixedRadiusArcCreator(1.5).intersects_with(Point(0, 0)).intersects_with(
            LineString([(-1, 2), (1, 2)])).create_circles()
        self.assertEqual(2, len(result))
        self.assertAlmostEqual(result[0].centroid.y, result[1].centroid.y)

    def test_create_circles_by_1_point_and_1_circle(self):
        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(Circle((0, 0), radius=10))

        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(Circle((0, 3.5), radius=1))

        result = FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(
            Circle((0, 2), radius=1)).create_circles()
        self.assertEqual(2, len(result))
        self.assertAlmostEqual(result[0].centroid.y, result[1].centroid.y)
        self.assertAlmostEqual(1, result[0].radius)

    def test_create_circles_by_2_lines(self):
        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(LineString([(-1, 0), (1, 0)])).intersects_with(
                LineString([(-1, 3), (1, 3)])).create_circles()

        with self.assertRaises(RuntimeError):
            _ = (FixedRadiusArcCreator(1)
                 .intersects_with(LineString([(-1, 0), (1, 0)]))
                 .intersects_with(LineString([(-1, 2), (1, 2)]))
                 .create_circles())

        result = (FixedRadiusArcCreator(1)
                  .intersects_with(LineString([(-1, 0), (1, 0)]))
                  .intersects_with(LineString([(-1, 2), (1, 2)]))
                  .intersects_with(Point(0, 1))
                  .create_circles())
        self.assertEqual(2, len(result))
        self.assertAlmostEqual(1, result[0].centroid.y)
        self.assertAlmostEqual(1, result[1].centroid.y)

        result = (FixedRadiusArcCreator(1)
                  .intersects_with(LineString([(-1, 0), (1, 0)]))
                  .intersects_with(LineString([(0, 1), (1, -1)]))
                  .create_circles())
        self.assertEqual(4, len(result))

    def test_create_circles_by_1_line_and_1_circle(self):
        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(LineString([(-1, 0), (1, 0)])).intersects_with(
                Circle((0, 10), radius=1)).create_circles()

        result = (FixedRadiusArcCreator(1)
                  .intersects_with(LineString([(-1, 0), (1, 0)]))
                  .intersects_with(Circle((0, 3), radius=1))
                  .create_circles())
        self.assertEqual(1, len(result))

        result = (FixedRadiusArcCreator(1.5)
                  .intersects_with(LineString([(-1, 0), (1, 0)]))
                  .intersects_with(Circle((0, 3), radius=1))
                  .create_circles())
        self.assertEqual(2, len(result))
        self.assertAlmostEqual(result[0].centroid.y, result[1].centroid.y)

        result = (FixedRadiusArcCreator(1.5)
                  .intersects_with(LineString([(-1, 0), (1, 0)]))
                  .intersects_with(Circle((0, 0), radius=1))
                  .create_circles())
        self.assertEqual(4, len(result))
        result.sort(key=lambda circle: circle.centroid.y)
        self.assertAlmostEqual(result[0].centroid.y, result[1].centroid.y)
        self.assertAlmostEqual(result[2].centroid.y, result[3].centroid.y)
        self.assertFalse(isclose(result[1].centroid.y, result[2].centroid.y))

        result = (FixedRadiusArcCreator(1.5)
                  .intersects_with(LineString([(-1, 0), (1, 0)]))
                  .intersects_with(Circle((0, 0), radius=10))
                  .create_circles())
        self.assertEqual(8, len(result))
        result.sort(key=lambda circle: circle.centroid.y)
        self.assertAlmostEqual(result[0].centroid.y, result[1].centroid.y)
        self.assertAlmostEqual(result[1].centroid.y, result[2].centroid.y)
        self.assertAlmostEqual(result[2].centroid.y, result[3].centroid.y)

        self.assertAlmostEqual(result[4].centroid.y, result[5].centroid.y)
        self.assertAlmostEqual(result[5].centroid.y, result[6].centroid.y)
        self.assertAlmostEqual(result[6].centroid.y, result[7].centroid.y)

        self.assertFalse(isclose(result[3].centroid.y, result[4].centroid.y))

    def test_create_circles_by_2_circles(self):
        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(Circle((0, 0), radius=1)).intersects_with(
                Circle((0, 10), radius=1)).create_circles()

        result = FixedRadiusArcCreator(1).intersects_with(Circle((0, 0), radius=1)).intersects_with(
            Circle((0, 4), radius=1)).create_circles()
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].centroid.almost_equals(Point(0, 2)))

        result = (FixedRadiusArcCreator(1.5)
                  .intersects_with(Circle((0, 0), radius=1))
                  .intersects_with(Circle((0, 4), radius=1))
                  .create_circles())
        self.assertEqual(2, len(result))
        self.assertAlmostEqual(result[0].centroid.y, result[1].centroid.y)

        result = (FixedRadiusArcCreator(1)
                  .intersects_with(Circle((0, 0), radius=2))
                  .intersects_with(Circle((0, 4), radius=2))
                  .create_circles())
        self.assertEqual(4, len(result))
        result.sort(key=lambda circle: circle.centroid.x)
        self.assertAlmostEqual(result[0].centroid.y, result[-1].centroid.y)
        self.assertAlmostEqual(result[1].centroid.x, result[1].centroid.x)

        result = (FixedRadiusArcCreator(1)
                  .intersects_with(Circle((0, 0), radius=2))
                  .intersects_with(Circle((0, 3.5), radius=2))
                  .create_circles())
        self.assertEqual(6, len(result))
        result.sort(key=lambda circle: circle.centroid.y)
        self.assertAlmostEqual(result[0].centroid.y, result[1].centroid.y)
        self.assertAlmostEqual(result[2].centroid.y, result[3].centroid.y)
        self.assertAlmostEqual(result[4].centroid.y, result[5].centroid.y)

    def test_create_arcs_by_2_circles(self):
        result = (FixedRadiusArcCreator(1)
                  .intersects_with(Circle((0, 0), radius=2))
                  .intersects_with(Circle((0, 3.5), radius=2))
                  .create_arcs())
        self.assertEqual(12, len(result))


class FixedCenterCircleCreatorTest(TestCase):
    def test_create_circles_by_point(self):
        result = (FixedCenterArcCreator((0, 0))
                  .intersects_with(Point(0, 1))
                  .create_circles())
        self.assertEqual(1, len(result))
        self.assertEqual(Point(0, 0), result[0].centroid)
        self.assertTrue(result[0].distance(Point(1, 0)) < MATH_EPS)

        with self.assertRaises(RuntimeError):
            (FixedCenterArcCreator((0, 0))
             .intersects_with(Point(0, 1))
             .intersects_with(Point(1, 1))
             .create_circles())

    def test_create_circles_by_line(self):
        result = (FixedCenterArcCreator((0, 0))
                  .intersects_with(LineString([(-1, 1), (100, 1)]))
                  .create_circles())
        self.assertEqual(1, len(result))

        with self.assertRaises(RuntimeError):
            (FixedCenterArcCreator((0, 0))
             .intersects_with(LineString([(-1, 1), (100, 1)]))
             .intersects_with(LineString([(-1, 2), (1, 2)]))
             .create_circles())

    def test_create_circles_by_circle_when_center_outside_circle(self):
        result = (FixedCenterArcCreator((0, 0))
                  .intersects_with(Circle((0, 10), radius=1))
                  .create_circles())
        self.assertEqual(2, len(result))
        result.sort(key=lambda circle: circle.radius)
        self.assertAlmostEqual(9, result[0].radius)
        self.assertAlmostEqual(11, result[1].radius)

    def test_create_circles_by_circle_when_center_inside_circle(self):
        result = (FixedCenterArcCreator((0, 0))
                  .intersects_with(Circle((0, 1), radius=2))
                  .create_circles())
        self.assertEqual(2, len(result))
        result.sort(key=lambda circle: circle.radius)
        self.assertAlmostEqual(1, result[0].radius)
        self.assertAlmostEqual(3, result[1].radius)

    def test_create_circles_by_circle_and_line(self):
        result = (FixedCenterArcCreator((0, 0))
                  .intersects_with(Circle((0, 10), radius=1))
                  .intersects_with(LineString([(9, -1), (9, 1)]))
                  .create_circles())
        self.assertEqual(1, len(result))

        with self.assertRaises(RuntimeError):
            (FixedCenterArcCreator((0, 0))
             .intersects_with(Circle((0, 10), radius=1))
             .intersects_with(LineString([(10, -1), (10, 1)]))
             .create_circles())

    def test_create_arcs_by_circle_and_line(self):
        result = (FixedCenterArcCreator((0, 0))
                  .intersects_with(Circle((0, 10), radius=1))
                  .intersects_with(LineString([(9, -1), (9, 1)]))
                  .create_arcs())
        self.assertEqual(2, len(result))
