from random import random
from unittest import TestCase

from shapely.extension.constant import MATH_EPS
from shapely.extension.strategy.decompose_strategy import CurveDecomposeStrategy
from shapely.extension.util.ccw import ccw
from shapely.extension.util.geom_offset_v2 import offset
from shapely.extension.util.line_extent_util import closed_ring_rebuild, group_by_line_extent
from shapely.geometry import LineString, LinearRing, Polygon


from shapely.wkt import loads


class ClosedRingRebuildTest(TestCase):
    def test_rebuild_ring_to_form_a_polygon_without_holes(self):
        poly = ccw(loads(
            "POLYGON ((-73 21, -35 21, -37 -21, -82 -24, -81 -23.5, -80 -23, -79 -22.5, -78 -22, -77 -21.25, -76 -20.5, -75 -19.75, -74 -19.25, -73.25 -18.25, -72.5 -17.5, -71.75 -16.75, -71 -16, -70.75 -15, -70.5 -14, -70.25 -13, -70 -12, -70 -11, -70.25 -10, -70.5 -9, -71 -8, -71.75 -7.25, -72.5 -6.5, -73 21))"))
        lines = poly.ext.decompose(LineString, CurveDecomposeStrategy(40)).to_list()
        self.assertEqual(5, len(lines))  # prerequisite of this testcase

        for _ in range(10):
            offset_lines = [offset(line, dist=random() * 5, side='left') for line in lines]
            result = closed_ring_rebuild(offset_lines)
            self.assertTrue(isinstance(result, LinearRing))
            self.assertTrue(result.is_valid)
            self.assertFalse(result.is_empty)
            self.assertTrue(Polygon(result).within(poly))
            self.assertTrue(Polygon(result).is_valid)

    def test_rebuild_exterior_having_both_positive_and_negative_angle(self):
        poly = ccw(loads("POLYGON ((-25 35, 14 34, 14 -3, 6 9, -10 -6, -30 -6, -8 10, -26 10, -25 35))"))
        lines = poly.ext.decompose(LineString, CurveDecomposeStrategy(10)).to_list()
        self.assertEqual(8, len(lines))

        for _ in range(10):
            offset_lines = [offset(line, dist=random() * 2, side='left') for line in lines]
            result = closed_ring_rebuild(offset_lines)
            self.assertTrue(isinstance(result, LineString) and result.is_valid and not result.is_empty)
            self.assertTrue(Polygon(result).within(poly))

    def test_rebuild_ring_by_large_offset_dist(self):
        poly = ccw(loads(
            "POLYGON ((-31 35, -6 35, -6.2 32.5, -13.6 32.4, -13.6 26.6, -7 26, -7 11, -30 11, -30 15, -12 15, -12 22, -31 22, -31 35))"))
        lines = poly.ext.decompose(LineString, CurveDecomposeStrategy(10)).to_list()
        self.assertEqual(12, len(lines))

        for _ in range(10):
            offset_lines = [offset(line, dist=random() * 2, side='left') for line in lines]
            if any(line.disjoint(poly) for line in offset_lines):
                continue

            result = closed_ring_rebuild(offset_lines)
            self.assertTrue(isinstance(result, LineString) and result.is_valid and not result.is_empty)
            self.assertTrue(Polygon(result).within(poly))


class GroupByLineExtentTest(TestCase):
    def assert_geometries_almost_equal(self, geom0, geom1, delta=MATH_EPS):
        return geom0.buffer(delta).contains(geom1) and geom1.buffer(MATH_EPS).contains(geom0)

    def test_group_by_line_extent_given_2_parallel_edge_segments(self):
        multiline = loads(
            "MULTILINESTRING ((-100 20, -100 15), (-98 14, -98 10), (-100 8, -100 5), (-98 5, -93 5), (-91 5, -91 18), (-92 20, -97 20))")
        segments = list(multiline.geoms)

        exterior_groups = group_by_line_extent(segments)
        self.assertEqual(2, len(exterior_groups))

        exterior_groups.sort(key=lambda l: l.length)
        self.assert_geometries_almost_equal(loads("LINESTRING (-98 14, -98 10)"), exterior_groups[0])
        self.assert_geometries_almost_equal(loads("LINESTRING (-100 15, -100 20, -91 20, -91 5, -100 5, -100 8)"),
                                            exterior_groups[1])

    def test_group_by_line_extent_given_0_parallel_edge_segments(self):
        multiline = loads(
            "MULTILINESTRING ((-102 19, -99 19), (-99 18, -98 17), (-99 16, -101.5 16), (-102 17, -102 17.5))")
        segments = list(multiline.geoms)

        exterior_groups = group_by_line_extent(segments)
        self.assertEqual(1, len(exterior_groups))

        self.assert_geometries_almost_equal(
            LinearRing(loads("LINESTRING (-102 19, -100 19, -97 16, -102 16, -102 19)")),
            exterior_groups[0])
        self.assertTrue(exterior_groups[0].is_closed)

    def test_group_by_line_extent_edge_segments_and_makes_no_boundary_ring(self):
        multiline = loads("MULTILINESTRING ((-110 30, -105 30), (-105 25, -95 25), (-90 30, -90 15))")
        segments = list(multiline.geoms)

        exterior_groups = group_by_line_extent(segments)
        self.assertEqual(2, len(exterior_groups))

        exterior_groups.sort(key=lambda l: l.length)
        self.assert_geometries_almost_equal(LineString([(-110, 30), (-105, 30)]), exterior_groups[0])
        self.assert_geometries_almost_equal(LineString([(-105, 25), (-90, 25), (-90, 15)]), exterior_groups[1])

    def test_group_by_line_extent_by_real_proj0(self):
        lines = [
            loads('LINESTRING (71.95132099821149 38.33929367121132, 75.66767194045951 55.35171583340991)'),
            loads('LINESTRING (80.43019006459119 46.20539115090506, 40.34016798203422 62.94673153758632)'),
            loads('LINESTRING (42.04662399721129 67.7587776584673, -55.26662629103956 107.6092729801434)'),
            loads('LINESTRING (-44.77466076446677 111.9881129837094, -50.90166567263173 97.14049202152171)'),
            loads('LINESTRING (-50.29836851811658 99.91670159287504, -55.65881300722638 -46.5022997340212)'),
            loads('LINESTRING (-56.1896458495756 -43.31890141056889, -51.51455317542407 -55.47848408740052)'),
            loads('LINESTRING (-53.13218663601797 -52.88667502184081, -25.3891233795242 -82.73274440667275)'),
            loads('LINESTRING (-23.42079732940007 -89.93175102176339, -27.93121343298523 -110.5752523672973)'),
            loads('LINESTRING (-34.07768121366949 -100.9923989896061, -21.40720560517489 -103.7602549453596)'),
            loads('LINESTRING (-23.3439728717884 -103.5777666207662, 41.72170866844422 -101.8089055556132)'),
            loads('LINESTRING (36.97771800363833 -103.5176709130603, 44.06773612516398 -97.96630244787885)'),
            loads('LINESTRING (41.16596061929589 -102.5865259870842, 51.29260528093165 -56.23056128735058)'),
            loads('LINESTRING (59.2530508939329 -19.78985911890082, 68.30189934354641 21.63325519372678)'),
        ]

        groups = group_by_line_extent(lines, parallel_as_separate_group=True)
        self.assertEqual(2, len(groups))
