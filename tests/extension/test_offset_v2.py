from itertools import product
from math import sqrt
from unittest import TestCase

from shapely.extension.constant import MATH_EPS
from shapely.extension.util.geom_offset_v2 import self_intersection, offset
from shapely.geometry import LineString, Point, LinearRing, box
from shapely.ops import unary_union
from shapely.wkt import loads


class SelfIntersectionTest(TestCase):
    # TEST PLAN:
    # * wrong type input
    # * different lines
    # 0. empty line
    # 1. linestring
    #     1.1 linestring without self-intersection
    #     1.2 linestring with only 1 self-intersection
    #     1.3 linestring with multiple self-intersections
    #     1.4 linestring with redundant coordinates
    # 2. linearRing
    #     1.1 normal linearRing with only head connects to tail
    #     1.2 linearRing with extra self-intersection (twisted ring)
    def test_set_wrong_type_input(self):
        with self.assertRaises(TypeError):
            self_intersection(None)

    def test_empty_line(self):
        self.assertEqual(0, len(self_intersection(LineString())))

    def test_linestring_without_self_intersection(self):
        line = LineString([(0, 0), (1, 1)])
        self.assertEqual(0, len(self_intersection(line)))

    def test_linestring_with_coord_redundant(self):
        line = LineString([(0, 0)] + [(1, 1)] * 5 + [(2, 2)])
        result = self_intersection(line)
        self.assertEqual(1, len(result))
        self.assertTrue(Point(1, 1) in result)

    def test_linestring_with_1_intersection(self):
        line = LineString([(0, 0), (1, 0), (0, 1), (0, -1)])
        result = self_intersection(line)
        self.assertEqual(1, len(result))
        self.assertTrue(Point(0, 0) in result)

    def test_linestring_with_multiple_intersections(self):
        line = LineString([(0, 0), (10, 0), (1, 10), (1, -10), (2, -10), (2, 10)])
        intersection_points = self_intersection(line)
        self.assertTrue(Point(1, 0) in intersection_points)
        self.assertTrue(Point(2, 0) in intersection_points)

    def test_normal_linearRing(self):
        result = self_intersection(LinearRing([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]))
        self.assertEqual(1, len(result))
        self.assertTrue(Point(0, 0) in result)

    def test_linearRing_with_self_intersection(self):
        ring = LinearRing([(0, 0), (10, 0), (2, 10), (2, -10), (1, -10), (1, 10), (0, 0)])
        result = self_intersection(ring)
        self.assertEqual(3, len(result))
        self.assertTrue(Point(0, 0) in result)
        self.assertTrue(Point(1, 0) in result)
        self.assertTrue(Point(2, 0) in result)

    def test_self_intersection_cut_line_into_pieces(self):
        line = loads(
            'LINESTRING (-4.8 4.65, -3.75 4.5, -2.8 4.15, -1.85 3.7, -0.35 2.45, 0.35 1, 0.4 -0.5, -0.2 -2.05, -1.35 -3.2, -2.75 -3.7, -4.15 -3.7, -5.2 -2.85, -5.6 -1.4, -5.1 0, -4.25 0.55, -3 1.05, -1.65 1.4, -0.6 1.7, 0.7 1.95, 2.15 2.3)')
        result = self_intersection(line)
        pieces = list(line.difference(unary_union(result)).geoms)
        self.assertEqual(3, len(pieces))


class GeomOffsetTest(TestCase):
    # TEST PLAN:
    # * different lines
    # 0. empty line
    # 1. straight line
    #   1.0 very short
    #   1.1 with redundant point
    #   1.2 without redundant point
    # 2. linestring without self-intersection
    # 3. linestring with self-intersection
    #   3.1 linestring with self-intersection
    #   3.2 normal linearRing with head and tail connected
    #   3.3 linestring with self-overlapping
    #   3.4 linearRing with self-intersection(twisted ring)
    # * different params
    # 1. dist
    #   1.1 empty dist
    #   1.2 super large dist
    # 2. different side
    # 3. reverse coord order true or false
    def test_offset_0_dist(self):
        line = LineString([(0, 0), (1, 0)])
        for side in product(('left', 'right')):
            self.assertEqual(line, offset(line, dist=0, side=side, invert_coords=False))
            self.assertEqual(line.ext.inverse(), offset(line, dist=0, side=side, invert_coords=True))

    def test_offset_with_super_large_dist(self):
        line = box(0, 0, 1, 1).exterior
        for side, dist in product(('left', 'right'), (1e6, -1e6)):
            result = offset(line, side=side, dist=dist)
            self.assertTrue(isinstance(result, LineString))

    def test_offset_empty_line(self):
        line = LineString()
        self.assertTrue(line.is_empty)
        for dist, side, reversed in product((-1, 1, 1e6), ('left', 'right'), (True, False)):
            result = offset(line, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
            self.assertTrue(result.is_empty)
            self.assertFalse(line.intersects(result))

    def test_offset_very_short_line(self):
        line = LineString([(0, 0), (MATH_EPS, MATH_EPS)])
        for dist, side, reversed in product((-1, 1, 1e6), ('left', 'right'), (True, False)):
            result = offset(line, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
            self.assertFalse(line.intersects(result))

    def test_offset_straight_line_without_redundant_point(self):
        line = LineString([(1.11, 1.11), (sqrt(2), sqrt(3))])
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(line, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
            self.assertAlmostEqual(line.length, result.length)
            self.assertFalse(line.intersects(result))

    def test_offset_straight_line_with_redundant_point(self):
        line = LineString([(0, 0)] + [(1, 0)] * 10 + [(2, 0)])
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(line, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
            self.assertAlmostEqual(line.length, result.length)
            self.assertFalse(line.intersects(result))

    def test_offset_linestring_without_self_intersection(self):
        line_without_self_intersection = loads(
            'LINESTRING (-218 28, -186 30, -157 5, -165 -30, -200 -29, -200 -12, -223 -12, -223 -38, -241 -47, -219 -64, -172 -59)')
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(line_without_self_intersection, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
            self.assertFalse(line_without_self_intersection.intersects(result))

    def test_offset_linestring_with_self_intersection(self):
        line_with_self_intersection = loads(
            'LINESTRING (-242 16, -239 16, -236.2 15.8, -233.8 15, -231.2 14, -228.4 12.8, -225.4 11.6, -222.6 10.4, -220.2 9.2, -218 8, -216.2 7, -214.8 6, -213.8 5, -212.8 4.2, -212 3.2, -211.2 2.4, -210.6 1.4, -209.6 -0.2, -208.6 -2, -208 -3, -207.4 -4, -206.8 -5.4, -206.4 -6.6, -206 -7.8, -205.6 -8.8, -205.4 -10.2, -205.2 -11.6, -205.2 -13, -205.2 -14.6, -205.2 -16.2, -205.4 -18, -205.8 -20.2, -206.8 -22.4, -208 -25, -209.4 -27.4, -210.8 -30, -212.4 -32.4, -214 -34.2, -215.8 -35.6, -217.4 -37, -219 -37.8, -220.6 -38.6, -222.4 -39.2, -224.6 -39.6, -226.6 -40, -229 -40.2, -231.4 -40.4, -233.8 -40.4, -235.8 -40.4, -237.6 -40.2, -239 -39.8, -240.4 -39.4, -241.6 -38.6, -242.6 -37.8, -243.4 -37, -244.4 -35.4, -245 -34.4, -245.4 -33.4, -245.6 -32.2, -245.8 -31, -246 -29.6, -246 -28, -246 -26.4, -246 -24.6, -245.8 -22.8, -245.4 -21, -245 -19.6, -244.4 -18.4, -244 -17.4, -243.4 -16.4, -242.4 -14.8, -241.4 -13.4, -240.4 -12, -239.2 -10.6, -238.2 -9.2, -237.2 -8, -236.2 -6.6, -235.2 -5.4, -234 -4.2, -233.2 -3.4, -231.8 -2, -230.8 -1.2, -230 -0.4, -229.2 0.2, -228.4 1, -227.6 1.6, -226 2.8, -225.2 3.6, -224.4 4.4, -223.6 5, -222 6.2, -221.2 6.8, -219.8 8, -218.4 8.8, -217.4 9.6, -216.2 10.2, -215 11, -213.6 11.8, -212.4 12.6, -211 13.2, -209.6 14, -208.2 14.6, -207 15.2, -205.8 15.8, -204.8 16.2, -203 16.8, -201.6 17.4, -200.4 17.8, -199.4 18, -199 18)')
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(line_with_self_intersection, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))

    def test_normal_linearRing(self):
        ring = loads(
            'POLYGON ((-236 6, -238.45 5.85, -239 2, -234 -3, -229.8 1.5, -234.3 1.5, -233.35 3.1, -228.5 8.35, -236 6))').exterior
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(ring, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
            self.assertEqual(result.coords[0], result.coords[-1])

        ring = box(0, 0, 5, 5).exterior
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(ring, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
            self.assertEqual(result.coords[0], result.coords[-1])

    def test_linestring_with_self_overlapping(self):
        line1 = LineString([(-1, 0), (1, 0), (-1, 0)])
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(line1, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))

        line2 = loads('LINESTRING (-1 1, -1 0.5, -0.5 0.5, -0.5 1, -0.3 1, -0.5 1, -0.5 0.5, -1 0.5, -1 1)')
        for dist, side in product((-1, 1), ('left', 'right')):
            result = offset(line2, dist=dist, side=side)
            self.assertTrue(isinstance(result, LineString))

    def test_linearRing_with_self_intersection(self):
        ring = LinearRing([(0, 0), (10, 0), (10, 5), (5, 5), (5, -5), (0, -5), (0, 0)])
        for dist, side, reversed in product((-1, 1), ('left', 'right'), (True, False)):
            result = offset(ring, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))

    def test_with_problematic_line(self):
        problematic_line = LinearRing(loads(
            "LINESTRING (-238.4819631795918 -67.02811230259515, -128.757776379829 -67.02811230259515, -128.7577763791686 -61.66716337834522, -127.907775478626 -61.66716328814685, -127.9077753884277 -60.86224509112085, -16.21137097833905 -60.86224509302351, -16.21137097833905 -53.46241763321262, -16.21133425774971 -53.29694340751365, -16.21133425782459 -3.210202105847194, -19.51522231407104 11.98439935326031, -21.70870993350916 17.85588257999631, -21.70880126665405 17.85584846410867, -22.49358680737618 19.95682509689262, -23.16238239565383 21.74704357995527, -23.16230457219972 21.74707265488018, -25.94493668373811 29.19655374317452, -144.7542067292072 -15.11571522608856, -146.6157136351928 -10.15870642229275, -238.4819631795547 -44.65726290349005, -238.4819631795918 -67.02811230259515)"))

        for dist, side, reversed in product((-10, 10), ('left', 'right'), (True, False)):
            result = offset(problematic_line, dist=dist, side=side, invert_coords=reversed)
            self.assertTrue(isinstance(result, LineString))
