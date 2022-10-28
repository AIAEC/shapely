from typing import List
from unittest import TestCase

from shapely.extension.geometry import StraightSegment
from shapely.extension.model.interval import Interval
from shapely.extension.strategy.bypassing_strategy import LongerBypassingStrategy
from shapely.extension.util.func_util import lmap
from shapely.geometry import Point, LineString, box


class LineStringExtensionTest(TestCase):
    def test_projected_point(self):
        # projected point on extension
        line = LineString([(0, 0), (1, 0)])
        result = line.ext.projected_point(Point(100, 1))
        self.assertTrue(result.equals(Point(100, 0)))

        result = line.ext.projected_point(Point(-100, 1))
        self.assertTrue(result.equals(Point(-100, 0)))

        result = line.ext.projected_point(Point(0.5, -1))
        self.assertTrue(result.equals(Point(0.5, 0)))

        # projected point not on extension
        result = line.ext.projected_point(Point(100, 1), on_extension=False)
        self.assertTrue(result.equals(Point(1, 0)))

        result = line.ext.projected_point(Point(-100, 1), on_extension=False)
        self.assertTrue(result.equals(Point(0, 0)))

        result = line.ext.projected_point(Point(0.6, 2), on_extension=False)
        self.assertTrue(result.equals(Point(0.6, 0)))

    def test_getitem(self):
        line = LineString([(i, 0) for i in range(0, 100)])
        self.assertEqual(line.ext[0], Point(0, 0))
        self.assertEqual(line.ext[-1], Point(99, 0))
        self.assertEqual(LineString([(0, 0), (1, 0)]), line.ext[:2])

    def test_substring(self):
        line = LineString([(0, 0), (100, 0)])
        result = line.ext.substring((0, 10))
        self.assertEqual(result, LineString([(0, 0), (10, 0)]))

    def test_inverse(self):
        line = LineString([(0, 0), (100, 0)])
        result = line.ext.inverse()
        self.assertEqual(LineString([(100, 0), (0, 0)]), result)

    def test_start_and_end(self):
        line = LineString([(0, 0), (100, 0)])
        self.assertEqual(Point(0, 0), line.ext.start())
        self.assertEqual(Point(100, 0), line.ext.end())

    def test_prolong(self):
        line = LineString([(0, 0), (1, 0), (1, 1)])
        result = line.ext.prolong().from_head(1)
        self.assertEqual(LineString([(-1, 0), (1, 0), (1, 1)]), result)

        result = line.ext.prolong().from_tail(1)
        self.assertEqual(LineString([(0, 0), (1, 0), (1, 2)]), result)

        result = line.ext.prolong().from_ends(1)
        self.assertEqual(LineString([(-1, 0), (1, 0), (1, 2)]), result)

        # given_end 是否需要在 line上？
        result = line.ext.prolong().from_end((0, 0.5), 2)
        self.assertEqual(LineString([(-2, 0), (1, 0), (1, 1)]), result)

        result = line.ext.prolong().from_end((1.5, 1), 2)
        self.assertEqual(LineString([(0, 0), (1, 0), (1, 3)]), result)

    def test_bypass(self):
        line = LineString([(0, 0), (10, 0)])
        obstacle = box(1, -1, 2, 2)
        result = line.ext.bypass(obstacle)
        self.assertTrue(isinstance(result, LineString))
        self.assertTrue(result.intersects(obstacle.buffer(1e-12)))
        self.assertFalse(result.intersects(obstacle.buffer(-1e-12)))

        result1 = line.ext.bypass(obstacle, LongerBypassingStrategy())
        self.assertTrue(isinstance(result1, LineString))
        self.assertTrue(result1.intersects(obstacle.buffer(1e-12)))
        self.assertFalse(result1.intersects(obstacle.buffer(-1e-12)))

        self.assertTrue(result.length < result1.length)

    def test_offset(self):
        line = LineString([(0, 0), (1, 0), (2, 0.5)])
        result = line.ext.offset(0.5, towards=Point(1, 2))
        result1 = line.ext.offset(0.5, towards='left')
        self.assertEqual(result, result1)

    def test_is_parallel_to(self):
        line0 = LineString([(0, 0), (1, 0)])
        line1 = LineString([(0, 1), (-1, 1.001)])
        self.assertTrue(line0.ext.is_parallel_to(line1, angle_tol=1))
        self.assertTrue(line0.ext.is_parallel_to(line1.ext.inverse(), angle_tol=1))
        self.assertFalse(line0.ext.is_parallel_to(line1))
        self.assertFalse(line0.ext.is_parallel_to(line1.ext.inverse()))

    def test_is_perpendicular_to(self):
        line0 = LineString([(0, 0), (1, 0)])
        line1 = LineString([(0, 0), (0.001, 1)])
        line2 = LineString([(0, 0), (0.001, -1)])
        self.assertFalse(line0.ext.is_perpendicular_to(line1))
        self.assertFalse(line0.ext.is_perpendicular_to(line2))
        self.assertTrue(line0.ext.is_perpendicular_to(line1, angle_tol=1))
        self.assertTrue(line0.ext.is_perpendicular_to(line2, angle_tol=1))

    def test_is_collinear_to(self):
        line0 = LineString([(0, 0), (1, 0)])
        line1 = LineString([(0, 1), (-1, 1.001)])
        line2 = LineString([(1, 0), (2, 0.001)])
        self.assertFalse(line0.ext.is_collinear_to(line1))
        self.assertFalse(line0.ext.is_collinear_to(line2))
        self.assertTrue(line0.ext.is_collinear_to(line2, angle_tol=1))

    def test_is_straight_line(self):
        line0 = LineString([(i, 0) for i in range(100)])
        self.assertTrue(line0.ext.is_straight())

        line1 = LineString([(0, 0), (1, 0.001), (2, -0.002)])
        self.assertFalse(line1.ext.is_straight())
        self.assertTrue(line1.ext.is_straight(1))

    def test_extend_to_merge(self):
        line0 = LineString([(0, 0), (1, 0)])
        line1 = LineString([(3, 1), (4, 2)])
        result = line0.ext.extend_to_merge(line1)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0), (3, 1), (4, 2)]).almost_equals(result))

    def test_projection_by(self):
        line0 = LineString([(i, 0) for i in range(100)])
        result = line0.ext.projection_by([box(0, 0, 1, 1), box(5, 0, 6, 1)])
        intervals = result.positive_intervals()
        self.assertEqual(2, len(intervals))
        intervals.sort()
        self.assertEqual(Interval(0, 1), intervals[0])
        self.assertEqual(Interval(5, 6), intervals[1])

    def test_perpendicular_line(self):
        arc = Point(0, 0).buffer(10).exterior
        result = arc.ext.perpendicular_line(Point(0, 11), 2)
        self.assertTrue(LineString([(0, 9), (0, 11)]).buffer(1e-6).contains(result))

    def test_tangent_line(self):
        arc = Point(0, 0).buffer(10).exterior
        result = arc.ext.tangent_line(Point(0, 11), 2)
        self.assertTrue(LineString([(-1, 10), (1, 10)]).buffer(1e-6).contains(result))

    def test_perpendicular_distance(self):
        line = LineString([(0, 0), (0, 1)])
        self.assertEqual(float('inf'), line.ext.perpendicular_distance(Point(0, 2)))
        self.assertEqual(float('inf'), line.ext.perpendicular_distance(Point(10, 2)))
        self.assertAlmostEqual(10, line.ext.perpendicular_distance(Point(10, 1)))

    def test_interpolate(self):
        line = LineString([(0, 0), (0, 1), (0, 2), (0, 3)])

        with self.assertRaises(TypeError):
            line.ext.interpolate(None)
            line.ext.interpolate('abc')

        self.assertListEqual(line.ext.interpolate([]), [])

        result = line.ext.interpolate(4, absolute=True)
        self.assertListEqual([Point(0, 4)], result)

        result = line.ext.interpolate(-1.5, absolute=False)
        self.assertListEqual([Point(0, -4.5)], result)

        result = line.ext.interpolate([-5.5, -1, 0, 3, 6], absolute=True)
        self.assertListEqual([Point(0, -5.5), Point(0, -1), Point(0, 0), Point(0, 3), Point(0, 6)], result)

        result = line.ext.interpolate([-2.0, -0.75, 0, 1, 1.25], absolute=False)
        self.assertListEqual([Point(0, -6), Point(0, -2.25), Point(0, 0), Point(0, 3), Point(0, 3.75)], result)

        result = line.ext.interpolate(range(-5, 6), absolute=True)
        self.assertEqual(11, len(result))
        self.assertListEqual([Point(0, i) for i in range(-5, 6)], result)

        line = LineString([(0, 0), (0, 1), (1, 1), (1, 0), (3, 0)])
        result = line.ext.interpolate(4, absolute=True)
        self.assertListEqual([Point(2, 0)], result)

        result = line.ext.interpolate(-1, absolute=False)
        self.assertListEqual([Point(0, -5)], result)

        result = line.ext.interpolate([-5.5, -1, 0, 3, 6], absolute=True)
        self.assertListEqual([Point(0, -5.5), Point(0, -1), Point(0, 0), Point(1, 0), Point(4, 0)], result)

        result = line.ext.interpolate([-2.0, -0.2, 0, 1, 1.2], absolute=False)
        self.assertListEqual([Point(0, -10), Point(0, -1), Point(0, 0), Point(3, 0), Point(4, 0)], result)

        result = line.ext.interpolate(map(lambda i: i / 5, range(6)), absolute=False)
        self.assertEqual(6, len(result))
        self.assertListEqual(lmap(lambda coord: Point(coord), [(0, 0), (0, 1), (1, 1), (1, 0), (2, 0), (3, 0)]), result)

    def test_segments(self):
        line = LineString([(0, 0), (0, 1)])
        segments = line.ext.segments()
        self.assertTrue(isinstance(segments, List))
        self.assertEqual(1, len(segments))
        self.assertTrue(all(isinstance(seg, StraightSegment) for seg in segments))
        self.assertEqual(segments[0], StraightSegment([(0, 0), (0, 1)]))

        line = LineString([(0, 0), (0, 1), (0, 2)])
        segments = line.ext.segments()
        self.assertTrue(isinstance(segments, List))
        self.assertEqual(2, len(segments))
        self.assertTrue(all(isinstance(seg, StraightSegment) for seg in segments))
        self.assertEqual(segments[0], StraightSegment([(0, 0), (0, 1)]))
        self.assertEqual(segments[1], StraightSegment([(0, 1), (0, 2)]))
