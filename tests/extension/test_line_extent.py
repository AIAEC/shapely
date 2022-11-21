from unittest import TestCase

from shapely.extension.constant import MATH_EPS
from shapely.extension.util.line_extent import LineExtent
from shapely.geometry import Point, LineString, LinearRing
from shapely.wkt import loads


class LineExtendTest(TestCase):
    def assert_geometries_almost_equal(self, geom0, geom1, delta=MATH_EPS):
        return geom0.buffer(delta).contains(geom1) and geom1.buffer(MATH_EPS).contains(geom0)

    def test_of_disjoint_sequence_lines_in_blunt_angle(self):
        line_ab = loads("LINESTRING (-100 0, -30 0)")
        line_cd = loads("LINESTRING (50 50, 100 100)")

        extent = LineExtent.of_sequence_curves(line_ab, line_cd)
        self.assertTrue(extent.extended_curve_ab.length > line_ab.length)
        self.assertTrue(extent.extended_curve_cd.length > line_cd.length)
        self.assert_geometries_almost_equal(extent.joint, Point(0, 0))
        self.assert_geometries_almost_equal(LineString([(-100, 0), (0, 0)]), extent.extended_curve_ab)
        self.assert_geometries_almost_equal(LineString([(0, 0), (100, 100)]), extent.extended_curve_cd)
        self.assert_geometries_almost_equal(LineString([(-100, 0), (0, 0), (100, 100)]), extent.merged_curve)

    def test_of_disjoint_sequence_lines_in_sharp_angle(self):
        line_ab = loads("LINESTRING (-100 0, -30 0)")
        line_cd = loads("LINESTRING (50 50, 0 100)")

        extent = LineExtent.of_sequence_curves(line_ab, line_cd)
        self.assertTrue(extent.extended_curve_ab.length > line_ab.length)
        self.assertTrue(extent.extended_curve_cd.length > line_cd.length)
        self.assert_geometries_almost_equal(extent.joint, Point(100, 0))
        self.assert_geometries_almost_equal(LineString([(-100, 0), (100, 0)]), extent.extended_curve_ab)
        self.assert_geometries_almost_equal(LineString([(100, 0), (0, 100)]), extent.extended_curve_cd)
        self.assert_geometries_almost_equal(LineString([(-100, 0), (100, 0), (0, 100)]), extent.merged_curve)

    def test_of_joint_sequence_lines(self):
        line_ab = loads("LINESTRING (-100 0, -30 0)")
        line_cd = loads("LINESTRING (-70 -10, -50 10)")

        extend = LineExtent.of_sequence_curves(line_ab, line_cd)
        self.assertTrue(extend.extended_curve_ab.length < line_ab.length)
        self.assertTrue(extend.extended_curve_cd.length < line_cd.length)
        self.assert_geometries_almost_equal(extend.joint, Point(-60, 0))
        self.assert_geometries_almost_equal(LineString([(-100, 0), (-60, 0)]), extend.extended_curve_ab)
        self.assert_geometries_almost_equal(LineString([(-60, 0), (-50, 10)]), extend.extended_curve_cd)
        self.assert_geometries_almost_equal(LineString([(-100, 0), (-60, 0), (-50, 10)]), extend.merged_curve)

    def test_of_sequence_lines_when_cd_across_head_point_of_ab(self):
        line_ab = loads("LINESTRING (-101 0, -30 0)")
        line_cd = loads("LINESTRING (-100 0, -80 21)")

        extend = LineExtent.of_sequence_curves(line_ab, line_cd)
        self.assertEqual(1, extend.extended_curve_ab.length)
        self.assertEqual(line_cd.length, extend.extended_curve_cd.length)
        self.assert_geometries_almost_equal(extend.joint, Point(-100, 0))
        self.assertFalse(extend.extended_curve_ab.is_empty)
        self.assert_geometries_almost_equal(LineString([(-100, 0), (-80, 21)]), extend.extended_curve_cd)
        self.assert_geometries_almost_equal(LineString([(-101, 0), (-100, 0), (-80, 21)]), extend.merged_curve)

    def test_of_sequence_lines_when_cd_across_end_point_of_ab(self):
        line_ab = loads("LINESTRING (-100 0, -30 0)")
        line_cd = loads("LINESTRING (-40 -10, -19 11)")

        extend = LineExtent.of_sequence_curves(line_ab, line_cd)
        self.assertEqual(line_ab.length, extend.extended_curve_ab.length)
        self.assertTrue(extend.extended_curve_cd.length < line_cd.length)
        self.assert_geometries_almost_equal(extend.joint, Point(-30, 0))
        self.assert_geometries_almost_equal(LineString([(-100, 0), (-30, 0)]), extend.extended_curve_ab)
        self.assert_geometries_almost_equal(LineString([(-30, 0), (-19, 11)]), extend.extended_curve_cd)
        self.assert_geometries_almost_equal(LineString([(-100, 0), (-30, 0), (-19, 11)]), extend.merged_curve)

    def test_of_sequence_lines_when_cd_hasnt_reached_ab_yet(self):
        line_ab = loads('LINESTRING (-36.87717274694342 60.98549795830033, -37.11210860192859 7.560509581364583)')
        line_cd = loads('LINESTRING (-29.06174914728302 15.57511011683264, -32.60113718425078 15.57530238194849)')

        extend = LineExtent.of_sequence_curves(line_ab, line_cd)
        self.assertIsNotNone(extend)
        self.assertTrue(extend.extended_curve_cd.is_empty)
        self.assertFalse(extend.extended_curve_ab.is_empty)
        self.assertFalse(extend.both_extended_curve_valid)

    def test_of_sequence_curves(self):
        curve_ab = loads(
            "LINESTRING (-76 32, -82 29, -84 26, -84.5 25, -86 18, -85 13, -79 5, -76 3, -65 0, -49 0)")
        curve_cd = loads("LINESTRING (-40 10, -40 20, -47 26, -54 26, -61 24)")

        extend = LineExtent.of_sequence_curves(curve_ab, curve_cd)
        self.assertTrue(extend.extended_curve_ab.length > curve_ab.length)
        self.assertTrue(extend.extended_curve_cd.length > curve_cd.length)
        self.assert_geometries_almost_equal(Point(-40, 0), extend.joint)
        self.assertTupleEqual((-76, 32), extend.extended_curve_ab.coords[0])
        self.assertTupleEqual((-40, 0), extend.extended_curve_ab.coords[-1])
        self.assert_geometries_almost_equal(loads(
            "LINESTRING (-76 32, -82 29, -84 26, -84.5 25, -86 18, -85 13, -79 5, -76 3, -65 0, -49 0, -40 0)"),
            extend.extended_curve_ab)
        self.assert_geometries_almost_equal(loads("LINESTRING (-40 0, -40 10, -40 20, -47 26, -54 26, -61 24)"),
                                            extend.extended_curve_cd)
        self.assert_geometries_almost_equal(loads(
            "LINESTRING (-76 32, -82 29, -84 26, -84.5 25, -86 18, -85 13, -79 5, -76 3, -65 0, -49 0, -40 0, -40 10, -40 20, -47 26, -54 26, -61 24)"),
            extend.merged_curve)

    def test_of_sequence_curves_which_has_2_intersection_points(self):
        curve_ab = loads("LINESTRING (-80 0, -60 0)")
        curve_cd = loads(
            "LINESTRING (-50 5, -45 10, -41 10, -34.285714285714285 5.857142857142857, -34 6, -34.285714285714285 2.142857142857143, -34 2, -35 -2, -38.714285714285715 -6.714285714285714, -39 -7, -47 -11.285714285714286, -47 -11)")
        extend = LineExtent.of_sequence_curves(curve_ab, curve_cd)
        expected_merged = loads(
            "LINESTRING (-80 0, -55 0, -50 5, -45 10, -41 10, -34.285714285714285 5.857142857142857, -34 6, -34.285714285714285 2.142857142857143, -34 2, -35 -2, -38.714285714285715 -6.714285714285714, -39 -7, -47 -11.285714285714286, -47 -11)")
        self.assert_geometries_almost_equal(expected_merged, extend.merged_curve)
        self.assert_geometries_almost_equal(LineString([(-80, 0), (-55, 0)]), extend.extended_curve_ab)
        self.assert_geometries_almost_equal(loads(
            "LINESTRING (-55 0, -50 5, -45 10, -41 10, -34.285714285714285 5.857142857142857, -34 6, -34.285714285714285 2.142857142857143, -34 2, -35 -2, -38.714285714285715 -6.714285714285714, -39 -7, -47 -11.285714285714286, -47 -11)"),
            extend.extended_curve_cd)

    def test_of_sequence_curves_for_2_parallel_lines(self):
        curve_ab = LineString([(0, 0), (10, 0)])
        curve_cd = LineString([(20, 0), (30, 0)])
        extend = LineExtent.of_sequence_curves(curve_ab, curve_cd)
        self.assert_geometries_almost_equal(LineString([(0, 0), (30, 0)]), extend.merged_curve)
        self.assert_geometries_almost_equal(Point(15, 0), extend.joint)

        extend = LineExtent.of_sequence_curves(curve_ab, curve_cd, ignore_parallel=True)
        self.assertIsNone(extend)

    def test_of_sequence_curves_and_make_a_closed_ring(self):
        curve_ab = loads("LINESTRING (-60 10, -50 10, -50 -10, -60 -10)")
        curve_cd = loads("LINESTRING (-65 -5, -65 5)")
        extend = LineExtent.of_sequence_curves(curve_ab=curve_ab, curve_cd=curve_cd, make_closed=True)
        self.assert_geometries_almost_equal(LinearRing([(-65, 10), (-50, 10), (-50, -10), (-65, -10), (-65, 10)]),
                                            extend.merged_curve)
        self.assert_geometries_almost_equal(LineString([(-65, 10), (-50, 10), (-50, -10), (-65, -10)]),
                                            extend.extended_curve_ab)
        self.assert_geometries_almost_equal(LineString([(-65, -10), (-65, 10)]), extend.extended_curve_cd)

    def test_of_sequence_curves_with_short_line(self):
        curve_ab = loads("LINESTRING (23.21461345810886 16.29713571509774, 23.21461345810886 16.26634954592742)")
        curve_cd = loads("LINESTRING (23.21461345810886 16.26634954592742, 23.21461345810886 -22.00289123840575)")
        extend = LineExtent.of_sequence_curves(curve_ab=curve_ab, curve_cd=curve_cd)
        self.assert_geometries_almost_equal(curve_ab, extend.extended_curve_ab)
        self.assert_geometries_almost_equal(curve_cd, extend.extended_curve_cd)
        self.assert_geometries_almost_equal(LineString([curve_ab.coords[0], curve_cd.coords[-1]]), extend.merged_curve)

    def test_curve_back_linestring_extension(self):
        curve_ab = loads(
            'LINESTRING (57.1897561951074 -0.5444931868081699, 39.272336872096275 9.343560637945473, 39.27233687182982 37.56162193469444, 32.57337963265413 51.2380979620815, 32.572451667989604 63.489902315997824, -147.839775709154 63.476237702424065, -176.46151528527918 49.28081614415168, -176.4170832483861 49.19122935845721, -169.31722438199355 52.71252090558536)')
        curve_cd = loads('LINESTRING (-161.71597391143092 52.47259376444484, -148.55375215562657 44.87471268170515)')
        extend = LineExtent.of_sequence_curves(curve_ab, curve_cd)
        self.assertTrue(extend.extended_curve_ab.length > curve_ab.length)
        self.assertTrue(extend.extended_curve_cd.length > curve_cd.length)
        self.assertTrue(extend.joint.disjoint(curve_ab))
        self.assertTrue(extend.joint.disjoint(curve_cd))

    def test_2_curve_back_linestrings_extension(self):
        curve_ab = loads('LINESTRING (10 1, 0 1, 0 0, 8.45 0)')
        curve_cd = loads('LINESTRING (4 6, 4 -3, 5 -3, 5 4)')
        extend = LineExtent.of_sequence_curves(curve_ab, curve_cd)
        self.assertTrue(extend.merged_curve.equals(loads('LINESTRING (10 1, 4 1, 4 -3, 5 -3, 5 4)')))
