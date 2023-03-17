from copy import deepcopy
from typing import List
from unittest import TestCase

import pytest

import shapely.wkt
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.interval import Interval
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.bypassing_strategy import LongerBypassingStrategy
from shapely.extension.strategy.linemerge_strategy import as_longest_straight_line
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

        result = line.ext.projected_point(Point(100, 0))
        self.assertTrue(result.equals(Point(100, 0)))

        # projected point not on extension
        result = line.ext.projected_point(Point(100, 1), on_extension=False)
        self.assertTrue(result.equals(Point(1, 0)))

        result = line.ext.projected_point(Point(-100, 1), on_extension=False)
        self.assertTrue(result.equals(Point(0, 0)))

        result = line.ext.projected_point(Point(0.6, 2), on_extension=False)
        self.assertTrue(result.equals(Point(0.6, 0)))

        result = line.ext.projected_point(Point(0, 0))
        self.assertTrue(result.equals(Point(0, 0)))

        result = line.ext.projected_point(Point(1, 0))
        self.assertTrue(result.equals(Point(1, 0)))

        line = LineString([(-29.57617211884179, 5.776949283250175), (-35.18104156096024, -13.72944278524371)])
        point = Point(-29.57617211884179, 5.776949283250175)
        result = line.ext.projected_point(point, on_extension=False)
        self.assertTrue(result.almost_equals(point))

        result = line.ext.projected_point(point, on_extension=True)
        self.assertTrue(result.almost_equals(Point(-29.57617211884179, 5.776949283250175)))

        line = LineString([(-42.05404584109783, -37.64927134883777), (-35.18104156096024, -13.72944278524371)])
        point = Point(-29.57617211884179, 5.776949283250175)
        result = line.ext.projected_point(point, on_extension=False)
        self.assertTrue(result.equals(Point(-35.18104156096024, -13.72944278524371)))

        result = line.ext.projected_point(point, on_extension=True)
        self.assertTrue(result.almost_equals(Point(-29.57617211884179, 5.776949283250175)))

    def test_projected_point_by_straight_segment(self):
        # projected point on extension
        straight_segment = StraightSegment([(0, 0), (1, 0)])
        result = straight_segment.ext.projected_point(Point(0, 0))
        self.assertTrue(result.equals(Point(0, 0)))

        result = straight_segment.ext.projected_point(Point(1, 0))
        self.assertTrue(result.equals(Point(1, 0)))

        result = straight_segment.ext.projected_point(Point(100, 1))
        self.assertTrue(result.equals(Point(100, 0)))

        # projected point not on extension
        result = straight_segment.ext.projected_point(Point(100, 1), on_extension=False)
        self.assertTrue(result.equals(Point(1, 0)))

        result = straight_segment.ext.projected_point(Point(0.6, 2), on_extension=False)
        self.assertTrue(result.equals(Point(0.6, 0)))

        straight_segment = StraightSegment(
            [(-29.57617211884179, 5.776949283250175), (-35.18104156096024, -13.72944278524371)])
        point = Point(-29.57617211884179, 5.776949283250175)
        result = straight_segment.ext.projected_point(point, on_extension=False)
        self.assertTrue(result.almost_equals(point))

        result = straight_segment.ext.projected_point(point, on_extension=True)
        self.assertTrue(result.almost_equals(Point(-29.57617211884179, 5.776949283250175)))

    def test_getitem(self):
        line = LineString([(i, 0) for i in range(0, 100)])
        self.assertEqual(line.ext[0], Point(0, 0))
        self.assertEqual(line.ext[-1], Point(99, 0))
        self.assertEqual(LineString([(0, 0), (1, 0)]), line.ext[:2])

    def test_substring(self):
        line = LineString([(0, 0), (100, 0)])
        result = line.ext.substring((0, 10))
        self.assertEqual(result, LineString([(0, 0), (10, 0)]))

    def test_substring_wont_change_interval(self):
        interval = Interval(100, 20)
        old_interval = deepcopy(interval)
        line = box(0, 0, 100, 100).exterior
        result = line.ext.substring(interval=interval, allow_circle=True)
        self.assertEqual(result, LineString([(100, 100), (0, 100), (0, 0), (100, 0), (100, 20)]))
        self.assertEqual(interval, old_interval)

    def test_reverse(self):
        line = LineString([(0, 0), (100, 0)])
        result = line.ext.reverse()
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
        self.assertTrue(line0.ext.is_parallel_to(line1.ext.reverse(), angle_tol=1))
        self.assertFalse(line0.ext.is_parallel_to(line1))
        self.assertFalse(line0.ext.is_parallel_to(line1.ext.reverse()))

        line2 = LineString([(-13.344930868732892, 31.590217663613032), (-18.99876411019792, 31.590542699372538)])
        line3 = LineString([(18.68523464902812, 31.58837626703631), (-13.334930868749396, 31.59021708871851)])
        self.assertTrue(line2.ext.is_parallel_to(line3))
        self.assertTrue(line2.ext.is_parallel_to(line3.ext.reverse()))

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
        line3 = LineString([(0, 0), (-1, 0)])
        self.assertFalse(line0.ext.is_collinear_to(line1))
        self.assertFalse(line0.ext.is_collinear_to(line2))
        self.assertTrue(line0.ext.is_collinear_to(line2, angle_tol=1))
        self.assertTrue(line0.ext.is_collinear_to(line3))

    def test_is_collinear_for_overlapping_lines(self):
        line0 = LineString([(0, 0), (1, 0)])
        line1 = LineString([(0.5, 0), (1.5, 0)])
        self.assertTrue(line0.ext.is_collinear_to((line1)))
        self.assertTrue(line1.ext.is_collinear_to((line0)))

    def test_is_collinear_to_for_short_lines(self):
        line0 = LineString([(0, 0), (0, 1)])
        line1 = LineString([(-1e-6, 0), (-1e-6, 1)])
        line0.ext.is_collinear_to(line1, angle_tol=2)

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
        self.assertTrue(LineString([(0, 0), (2, 0), (4, 2)]).almost_equals(result))

    def test_real_extend_to_merge(self):
        line0 = shapely.wkt.loads(
            "LINESTRING (40.19805392440635 -0.0013248190869355, 40.19805392440635 44.61139266384599, -40.205089850155204 44.61127537604853, -40.205089806597485 -44.61405404443773, 48.248053924451796 -44.61405404493709)")
        line1 = shapely.wkt.loads(
            "LINESTRING (40.19805392440635 -52.664054044937046, 40.19805392440635 -0.0013248190869319)")
        result = line0.ext.extend_to_merge(line1)
        assert isinstance(result, LineString)
        expected_poly = box(-40.205089850155204, -44.61405404443773, 40.198053924406324, 44.61127537604853)
        assert result.length == pytest.approx(expected_poly.exterior.length, abs=0.01)

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

        line = LineString([(0, 0), (1, 0)])
        result = line.ext.perpendicular_line(Point(0, 0), 1, 'left')
        self.assertTrue(LineString([(0, 0), (0, 1)]).equals(result))

        result = line.ext.perpendicular_line(Point(0, 0), 1, 'right')
        self.assertTrue(LineString([(0, 0), (0, -1)]).equals(result))

        result = line.ext.perpendicular_line(Point(1, 0), 1, 'left')
        self.assertTrue(LineString([(1, 0), (1, 1)]).equals(result))

        result = line.ext.perpendicular_line(Point(1, 0), 1, 'right')
        self.assertTrue(LineString([(1, 0), (1, -1)]).equals(result))

        result = line.ext.perpendicular_line(Point(0.5, 0), 1, 'left')
        self.assertTrue(LineString([(0.5, 0), (0.5, 1)]).equals(result))

        result = line.ext.perpendicular_line(Point(0.5, 0), 1, 'right')
        self.assertTrue(LineString([(0.5, 0), (0.5, -1)]).equals(result))

    def test_perpendicular_line_eps(self):
        segment = shapely.wkt.loads(
            "LINESTRING (489022.2789287367 2493968.052269809, 489022.264108756 2493967.8528196453)")
        result = segment.ext.perpendicular_line(segment.centroid, 1, 'left')
        assert result == shapely.wkt.loads(
            'LINESTRING (489023.2671529724 2493967.8592040185, 489022.27151874633 2493967.9525447274)')
        assert result.length == pytest.approx(1)

    def test_tangent_line(self):
        arc = Point(0, 0).buffer(10).exterior
        result = arc.ext.tangent_line(Point(0, 11), 2)
        self.assertTrue(LineString([(-1, 10), (1, 10)]).buffer(1e-6).contains(result))

    def test_perpendicular_distance(self):
        line = LineString([(0, 0), (0, 1)])
        self.assertEqual(float(0), line.ext.perpendicular_distance(Point(0, 2)))
        self.assertEqual(float(10), line.ext.perpendicular_distance(Point(10, 2)))
        self.assertAlmostEqual(10, line.ext.perpendicular_distance(Point(10, 1)))

    def test_interpolate(self):
        line = LineString([(0, 0), (0, 1), (0, 2), (0, 3)])

        with self.assertRaises(TypeError):
            line.ext.interpolate(None)
            line.ext.interpolate('abc')

        self.assertEqual(Point(0, 0), line.ext.interpolate(0))

        self.assertListEqual(line.ext.interpolate([]), [])

        result = line.ext.interpolate(4, absolute=True)
        self.assertEqual(Point(0, 4), result)

        result = line.ext.interpolate(-1.5, absolute=False)
        self.assertEqual(Point(0, -4.5), result)

        result = line.ext.interpolate([-5.5, -1, 0, 3, 6], absolute=True)
        self.assertListEqual([Point(0, -5.5), Point(0, -1), Point(0, 0), Point(0, 3), Point(0, 6)], result)

        result = line.ext.interpolate([-2.0, -0.75, 0, 1, 1.25], absolute=False)
        self.assertListEqual([Point(0, -6), Point(0, -2.25), Point(0, 0), Point(0, 3), Point(0, 3.75)], result)

        result = line.ext.interpolate(range(-5, 6), absolute=True)
        self.assertEqual(11, len(result))
        self.assertListEqual([Point(0, i) for i in range(-5, 6)], result)

        line = LineString([(0, 0), (0, 1), (1, 1), (1, 0), (3, 0)])
        result = line.ext.interpolate(4, absolute=True)
        self.assertEqual(Point(2, 0), result)

        result = line.ext.interpolate(-1, absolute=False)
        self.assertEqual(Point(0, -5), result)

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

    def test_endpoints_vector(self):
        line = LineString([(0, 0), (0, 1)])
        vec = line.ext.endpoints_vector()
        self.assertTrue(isinstance(vec, Vector))
        self.assertEqual(Vector(0, 1), vec)

    def test_normal_vector(self):
        line = LineString([(0, 0), (0, 1)])
        vec = line.ext.normal_vector()
        self.assertTrue(isinstance(vec, Vector))
        self.assertEqual(Vector(-1, 0), vec)

    def test_merge_with_native_linemerge(self):
        line = LineString([(0, 0), (0, 1)])
        result = line.ext.merge(LineString([(0, 1), (0, 2)]))
        self.assertTrue(LineString([(0, 0), (0, 2)]).equals(result))

        result = line.ext.merge(LineString([(0, 2), (0, 3)]))
        self.assertTrue(line.equals(result))

    def test_merge_as_longest_straight_line(self):
        line = LineString([(0, 0), (1, 0)])
        result = line.ext.merge(LineString([(0.5, -0.1), (-1, 0)]), as_longest_straight_line)
        self.assertTrue(LineString([(1, 0), (-1, 0)]).equals(result))

    def test_substring_(self):
        line = LineString([(10, 0), (10, 10), (0, 10), (0, 0), (10, 0)])
        a = line.project(Point(5, 0))
        b = line.project(Point(10, 5))
        result = line.ext.substring([a, b], allow_circle=True)
        self.assertTrue(LineString([(5, 0), (10, 0), (10, 5)]).equals(result))

        result = line.ext.substring([a, b])
        self.assertTrue(LineString([(5, 0), (0, 0), (0, 10), (10, 10), (10, 5)]).equals(result))

        result = line.ext.substring([0, b], allow_circle=True)
        self.assertTrue(LineString([(10, 0), (10, 5)]).equals(result))

        result = line.ext.substring([0, a], allow_circle=True)
        self.assertTrue(LineString([(10, 0), (10, 10), (0, 10), (0, 0), (5, 0)]).equals(result))

        result = line.ext.substring([b, 0], allow_circle=True)
        self.assertTrue(LineString([(10, 5), (10, 10), (0, 10), (0, 0), (10, 0)]).equals(result))

        result = line.ext.substring([a, 0], allow_circle=True)
        self.assertTrue(LineString([(5, 0), (10, 0)]).equals(result))
