from unittest import TestCase

import pytest

from shapely.extension.constant import MATH_EPS
from shapely.extension.functional import seq
from shapely.extension.model.interval import Interval
from shapely.extension.model.projection import Projection, shadow
from shapely.extension.model.vector import Vector
from shapely.geometry import LineString, box, Polygon, Point
from shapely.ops import unary_union
from shapely.wkt import loads


class ProjectionTest(TestCase):
    def test_shadow(self):
        geom0 = loads(
            'POLYGON ((-17.3 1.8, -19.4 1.8, -19.4 -4.3, -13 -4.3, -13.2 -2.5, -15.7 -2.7, -15.8 -0.8, -12.1 -1, -12.1 1.3, -17.1 1, -17.1 -2.6, -18 -2.6, -18.3 0.9, -17.8 1.3, -17.3 1.8))')
        shadow0 = shadow(geom=geom0, direction=Vector(1, 1), shadow_len=3)
        self.assertTrue(isinstance(shadow0, Polygon))
        self.assertTrue(shadow0.area > geom0.area)

        geom1 = Point(0, 0)
        shadow1 = shadow(geom=geom1, direction=Vector(1, 1), shadow_len=3)
        self.assertTrue(isinstance(shadow1, LineString))
        self.assertAlmostEqual(3, shadow1.length)

        geom2 = LineString([(0, 0), (1, 0.5)])
        shadow2 = shadow(geom=geom2, direction=Vector(1, 1), shadow_len=3)
        self.assertTrue(isinstance(shadow2, Polygon))

        geom3 = LineString([(0, 0), (1, 0)])
        shadow3 = shadow(geom=geom3, direction=Vector(-1, 0), shadow_len=3)
        self.assertTrue(isinstance(shadow3, LineString))
        self.assertFalse(shadow3.is_empty)

    def test_projection_onto_line_in_target(self):
        target_line = LineString([(0, 0), (100, 0)])

        projector_1 = LineString([(-10, 10), (40, 60)])
        result_1 = Projection(projector_1).onto(target_line)
        segments = result_1.segments
        positive_intervals = result_1.positive_intervals()
        negative_intervals = result_1.negative_intervals()
        self.assertEqual(1, len(segments))
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(1, len(negative_intervals))
        self.assertEqual(LineString([(0, 0), (40, 0)]), segments[0])

        projector_2 = LineString([(-10, 0), (-5, 0)])
        result_2 = Projection(projector_2).onto(target_line)
        segments = result_2.segments
        positive_intervals = result_2.positive_intervals()
        negative_intervals = result_2.negative_intervals(normalized=True)
        self.assertEqual(0, len(segments))
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(1, len(negative_intervals))
        self.assertEqual(0, negative_intervals[0].left)
        self.assertEqual(1, negative_intervals[0].right)

    def test_projection_onto_line_out_of_target(self):
        target_line = LineString([(0, 0), (100, 0)])

        projector_1 = LineString([(-10, 10), (40, 60)])
        result_1 = Projection(projector_1).onto(target_line, is_out_of_target=True)
        segments = result_1.segments
        positive_intervals = result_1.positive_intervals(normalized=True)
        negative_intervals = result_1.negative_intervals(normalized=True)
        positive_length = result_1.positive_length(normalized=True)
        negative_length = result_1.negative_length(normalized=True)

        self.assertEqual(1, len(segments))
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(1, len(negative_intervals))
        self.assertEqual(LineString([(-10, 0), (40, 0)]), segments[0])
        self.assertEqual(-0.1, positive_intervals[0].left)
        self.assertEqual(0.4, positive_intervals[0].right)
        self.assertEqual(0.4, negative_intervals[0].left)
        self.assertEqual(1, negative_intervals[0].right)
        self.assertEqual(0.5, positive_length)
        self.assertEqual(0.6, negative_length)

        projector_2 = LineString([(80, 10), (120, 10)])
        result_2 = Projection(projector_2).onto(target_line, is_out_of_target=True)
        segments = result_2.segments
        positive_intervals = result_2.positive_intervals(normalized=True)
        negative_intervals = result_2.negative_intervals(normalized=True)

        self.assertEqual(1, len(segments))
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(1, len(negative_intervals))
        self.assertEqual(LineString([(80, 0), (120, 0)]), segments[0])
        self.assertEqual(0.8, positive_intervals[0].left)
        self.assertEqual(1.2, positive_intervals[0].right)
        self.assertEqual(0, negative_intervals[0].left)
        self.assertEqual(0.8, negative_intervals[0].right)

    def test_projection_onto_line_by_direct(self):
        target_line = LineString([(0, 0), (100, 0)])
        projector = LineString([(0, 10), (20, 10)])

        segments_1 = Projection(projector).onto(target_line, direction=90).segments
        eps = 1e-4
        self.assertAlmostEqual(0, segments_1[0].coords[0][0], delta=eps)
        self.assertAlmostEqual(20, segments_1[0].coords[1][0], delta=eps)

        segments_2 = Projection(projector).onto(target_line, direction=45).segments
        self.assertAlmostEqual(0, segments_2[0].coords[0][0], delta=eps)
        self.assertAlmostEqual(10, segments_2[0].coords[1][0], delta=eps)

        segments_3 = Projection(projector).onto(target_line, direction=-45).segments
        self.assertAlmostEqual(10, segments_3[0].coords[0][0], delta=eps)
        self.assertAlmostEqual(30, segments_3[0].coords[1][0], delta=eps)

        segments_4 = Projection(projector).onto(target_line, direction=Vector.from_angle(45)).segments
        self.assertAlmostEqual(0, segments_4[0].coords[0][0], delta=eps)
        self.assertAlmostEqual(10, segments_4[0].coords[1][0], delta=eps)

    def test_polygon_projection_onto_line(self):
        target_line = LineString([(0, 0), (100, 0)])
        projector = box(-10, 10, 30, 30)

        segments_1 = Projection(projector).onto(target_line, is_out_of_target=False).segments
        self.assertEqual(LineString([(0, 0), (30, 0)]), segments_1[0])

        segments_2 = Projection(projector).onto(target_line, is_out_of_target=True).segments
        self.assertEqual(LineString([(30, 0), (-10, 0)]), segments_2[0])

    def test_cross_geom_projection_onto_line(self):
        target_line = LineString([(0, 0), (100, 0)])

        projector_1 = LineString([(-10, -20), (30, 20)])
        segments_1 = Projection(projector_1).onto(target_line, is_out_of_target=True).segments
        self.assertEqual(LineString([(-10, 0), (30, 0)]), segments_1[0])

        projector_2 = box(-10, -10, 30, 30)
        segments_2 = Projection(projector_2).onto(target_line).segments
        self.assertEqual(LineString([(0, 0), (30, 0)]), segments_2[0])

    def test_multipolygon_projection_onto_line(self):
        target_line = LineString([(0, 0), (100, 0)])
        box0 = box(1, 1, 2, 2)
        box1 = box(51, 1, 52, 2)
        projector = unary_union([box0, box1])
        result = Projection(projector).onto(target_line)

        segments = result.segments
        positive_intervals = result.positive_intervals()
        negative_intervals = result.negative_intervals()
        self.assertEqual(2, len(segments))
        self.assertEqual(2, len(positive_intervals))
        self.assertEqual(3, len(negative_intervals))

        positive_intervals.sort()
        self.assertEqual(Interval(1, 2), positive_intervals[0])
        self.assertEqual(Interval(51, 52), positive_intervals[1])

    def test_projection_onto_vertical(self):
        target_line = LineString([(0, 0), (0, 100)])
        projector = LineString([(-10, 10), (10, 10)])

        result_1 = Projection(projector).onto(target_line)
        segments = result_1.segments
        positive_intervals = result_1.positive_intervals(normalized=True)
        negative_intervals = result_1.negative_intervals(normalized=True)
        self.assertEqual(LineString([(0, 10), (0, 10)]), segments[0])
        self.assertEqual(0, positive_intervals[0].length)
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(2, len(negative_intervals))

        result_2 = Projection(projector).onto(target_line, direction=90)
        segments = result_2.segments
        positive_intervals = result_2.positive_intervals(normalized=True)
        negative_intervals = result_2.negative_intervals(normalized=True, eps=0)
        self.assertEqual(target_line, segments[0])
        self.assertEqual(1, positive_intervals[0].length)
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(0, len(negative_intervals))

    def test_projection_onto_parallel(self):
        target_line = LineString([(0, 0), (100, 0)])

        projector_1 = LineString([(-10, 10), (10, 10)])
        result_1 = Projection(projector_1).onto(target_line, direction=0)
        segments = result_1.segments
        positive_intervals = result_1.positive_intervals(normalized=True)
        negative_intervals = result_1.negative_intervals(normalized=True)

        self.assertEqual(0, len(segments))
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(1, len(negative_intervals))
        self.assertEqual(0, negative_intervals[0].left)
        self.assertEqual(1, negative_intervals[0].right)

        projector_2 = box(-3, -2, -1, 2)
        result_2 = Projection(projector_2).onto(target_line, direction=0)
        segments = result_2.segments
        positive_intervals = result_2.positive_intervals(normalized=True)
        negative_intervals = result_2.negative_intervals(normalized=True)

        self.assertEqual(1, len(segments))
        self.assertEqual(1, len(positive_intervals))
        self.assertEqual(0, len(negative_intervals))
        self.assertEqual(0, positive_intervals[0].left)
        self.assertEqual(1, positive_intervals[0].right)

    def assert_valid_shadow_between(self, shadow_between, projector, target):
        self.assertTrue(isinstance(shadow_between, Polygon))
        shadow_shrink = shadow_between.buffer(-MATH_EPS)
        self.assertFalse(shadow_shrink.intersects(projector))
        self.assertFalse(shadow_shrink.intersects(target))

        self.assertAlmostEqual(0, shadow_between.distance(projector), delta=MATH_EPS * 1e3)
        self.assertAlmostEqual(0, shadow_between.distance(target), delta=MATH_EPS * 1e3)

    def test_projection_towards_of_2_convex_polys(self):
        projector = loads('POLYGON ((-9.9 3.5, -11.4 -1.9, -8.2 -2.3, -8.2 -1.3, -6.6 -1.3, -5.8 3.5, -9.9 3.5))')
        target = loads('POLYGON ((-9.2 -4.6, -9.2 -5.6, -2.6 -6.9, -2.5 -5.8, -9.2 -4.6))')

        shadow_between = Projection(projector).towards(target, direction=Vector(0, -1)).shadow()
        self.assert_valid_shadow_between(shadow_between=shadow_between, projector=projector, target=target)

    def test_projection_towards_poly_and_fully_cover_it(self):
        projector = loads(
            'POLYGON ((-14.4 1.1, -14.6 -3.1, -13.2 -2.8, -13 -1.1, -4.7 -1.8, -4.6 -3.7, -2.8 -3.5, -3.6 0.5, -14.4 1.1))')
        target = loads(
            'POLYGON ((-8.7 -4.2, -11.7 -4.3, -12.3 -6.3, -10.4 -7.5, -6.3 -7.3, -6.3 -6, -10.3 -6.4, -10.8 -5.7, -7.2 -5, -8.7 -4.2))')

        shadow_between = Projection(projector).towards(target, direction=Vector(0, -1)).shadow()
        self.assert_valid_shadow_between(shadow_between=shadow_between, projector=projector, target=target)

    def test_projection_towards_between_line_and_poly(self):
        projector = loads('LINESTRING (-16.8 -0.5, -10.4 -0.1, -9 -1.6)')
        target = loads(
            'POLYGON ((-12.1 -3.1, -14.9 -3.1, -14.9 -5, -11.4 -5.6, -12.6 -4.7, -10.2 -4.7, -12.1 -3.1))')

        shadow_between0 = Projection(projector).towards(target, direction=Vector(0, -1)).shadow()
        self.assert_valid_shadow_between(shadow_between=shadow_between0, projector=projector, target=target)

        shadow_between1 = Projection(target).towards(projector, direction=Vector(0, 1)).shadow()
        self.assert_valid_shadow_between(shadow_between=shadow_between1, projector=projector, target=target)

        self.assertAlmostEqual(shadow_between0.area, shadow_between1.area)

    def test_projection_towards_and_expect_no_shadow(self):
        projector = box(0, 0, 1, 1)
        target = box(10, 10, 11, 11)

        shadow_between = Projection(projector).towards(target, direction=Vector(0, 1)).shadow()
        self.assertTrue(shadow_between.is_empty)

    def test_projection_of_line_towards_another_line(self):
        projector = LineString([(2, 0), (4, 0)])
        target = LineString([(-1, -1), (1, 1)])

        shadow_between = Projection(projector).towards(target, direction=Vector(-1, 0)).shadow()
        self.assertFalse(shadow_between.is_empty)
        self.assertTrue(shadow_between.distance(projector) < 1e-6)
        self.assertTrue(shadow_between.distance(target) < 1e-6)

    def test_projection_one_point_onto_straight_line_with_projection_direction_parallel_to_line(self):
        projector = Point(0, 10)
        target = LineString([(0, 0), (0, -10)])

        self.assertListEqual([Interval(0, 0)], Projection(projector).onto(target).positive_intervals())

    def test_parallels_to_check_tol(self):
        line0 = loads('LINESTRING (68.02162562938169 79.58384943260192, 104.96153865512305 79.58384943260192)')
        line1 = loads('LINESTRING (98.81181016021011 116.2232460161785, 55.27486062741048 116.24017796201451)')

        segs = Projection(line0).onto(line1).segments
        self.assertTrue(len(segs) > 0)

    def test_projection(self):
        l1: LineString = loads("LINESTRING (200 100, 0 -100)")
        o1: LineString = loads(
            "POLYGON ((92.22182682116156 0, 94.500001 2.278174178838449, 94.500001 0, 92.22182682116156 0))")
        negative_intervals = l1.ext.projection_by(o1).negative_intervals()

        self.assertEqual(2, len(negative_intervals))

    def test_projection_of_small_projector(self):
        obs = loads(
            "GEOMETRYCOLLECTION (POLYGON ((72.31927645643002 53.576712197850696, 72.31933140499405 30.74639189107678, 69.56933240500207 30.746385272313045, 69.56927745643806 53.57670557908696, 72.31927645643002 53.576712197850696)), LINESTRING (67.69474738542999 30.746380760516733, 67.01933340500939 30.74637913491412))")
        line = loads(
            "LINESTRING (67.01927745644537 53.576699441685626, 67.0193324050094 30.746379134911713)")
        line.ext.projection_by(obs).negative_intervals()  # assert no raise

    def test_projection_under_floating_error(self):
        projector = loads('LINESTRING (16.162333183815875 -50.612093227141756, 21.51233318381587 -50.612093227141756)')
        target = loads('LINESTRING (15.621890008496287 -33.28352178738958, 15.621890008496289 -59.11500092309821)')

        seg_results = Projection(projector).onto(target).segments
        self.assertTrue(len(seg_results) > 0)
        self.assertEqual(seg_results[0].length, 0)

    def test_projection_floating_error(self):
        line = loads('LINESTRING (144.0640604486713 31.58116830738623, 102.2051447298799 31.5835747533993)')
        projection1, projection2 = [
            seq(l.ext.projection_by(line).positive_intervals()).map(lambda interval: interval.length).sum() for l in
            [line, line.ext.reverse()]]
        assert projection1 == pytest.approx(projection2, abs=1e-10)
