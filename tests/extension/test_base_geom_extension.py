from math import isclose, sqrt
from unittest import TestCase

from shapely.extension.model import Vector, Angle, AlignLineString
from shapely.extension.strategy.decompose_strategy import StraightSegmentDecomposeStrategy
from shapely.geometry import Polygon, LineString, MultiLineString, box, Point


class BaseGeomExtensionTest(TestCase):
    def test_polygon(self):
        polygon = Polygon([(0, 0), (-1, 1), (0, 2), (1, 1)])

        # decompose
        edges = polygon.ext.decompose(LineString, StraightSegmentDecomposeStrategy())
        self.assertEqual(4, len(edges.to_list()))
        self.assertTrue(edges.map(lambda l: isclose(l.length, sqrt(2))).all())

        # flatten
        polys = polygon.ext.flatten()
        self.assertEqual(1, len(polys.to_list()))

        # envelope
        self.assertAlmostEqual(45, polygon.ext.envelope().tightened().angle.degree)
        self.assertAlmostEqual(0, polygon.ext.envelope().of_angle(0).angle.degree)

        # divided_by
        divider = MultiLineString([LineString([(0, -1), (0, 3)]),
                                   LineString([(-2, 1), (2, 1)])])
        result = polygon.ext.divided_by(divider)
        self.assertEqual(4, len(result.to_list()))
        self.assertTrue(result.map(lambda geom: isclose(geom.area, 0.5)).all())

        result = polygon.ext.divided_by([LineString([(0, -1), (0, 3)]),
                                         LineString([(-2, 1), (2, 1)])])
        self.assertEqual(4, len(result.to_list()))
        self.assertTrue(result.map(lambda geom: isclose(geom.area, 0.5)).all())

        # move_by
        self.assertTrue(polygon.ext.move_by(Vector(1, 0)).equals(Polygon([(1, 0), (2, 1), (1, 2), (0, 1)])))

        # move_to
        self.assertTrue(polygon.ext.move_to((0, 2)).equals(Polygon([(0, 1), (1, 2), (0, 3), (-1, 2)])))

        # rotate_ccw
        self.assertTrue(polygon.ext.rotate_ccw(90).equals(polygon))

        # scale
        self.assertAlmostEqual(polygon.area * 2, polygon.ext.scale(2).area)

        # ccw
        self.assertFalse(polygon.exterior.is_ccw)
        self.assertTrue(polygon.ext.ccw().exterior.is_ccw)

        # connect_path
        path = polygon.ext.connect_path(LineString([(1, 0), (2, 1)]))
        self.assertAlmostEqual(1 / sqrt(2), path.length)

        # difference
        result = polygon.ext.difference(box(-1, 0, 1, 2), component_buffer=0.001)
        self.assertTrue(result.is_empty)

        result = polygon.ext.difference(box(-1, 0, 1, 2), component_buffer=-0.001)
        self.assertFalse(result.is_empty)

        # intersection
        result = polygon.ext.intersection([LineString([(0, 0), (0, 1)]), LineString([(0, 1), (0, 2)])])
        self.assertTrue(isinstance(result, MultiLineString))

        # is_
        self.assertFalse(polygon.ext.is_('valid', 'empty'))
        self.assertTrue(polygon.ext.is_('valid', 'simple'))

        # angle
        self.assertEqual(Angle(45), polygon.ext.angle())

        # simplify
        self.assertTrue(polygon.ext.simplify()[0].equals(polygon))

        # move_towards
        result = polygon.ext.move_towards(LineString([(10, 0), (0, 10)]), direction=Vector(1, 0))
        self.assertTrue(result.equals(Polygon([(8, 0), (7, 1), (8, 2), (9, 1)])))

        # distance
        dist = polygon.ext.distance(LineString([(10, 0), (0, 10)]), direction=Vector(1, 0))
        self.assertAlmostEqual(8, dist)

        # alignment
        dists = polygon.ext.alignment().distances_to(AlignLineString(LineString([(0, 0), (1, -1)])))
        dists.sort()
        self.assertAlmostEqual(0, dists[0])
        self.assertAlmostEqual(sqrt(2), dists[1])

        # f_distance
        pts = [Point(0, 2), Point(0, 100)]
        pts = list(filter(polygon.ext.f_distance() < 10, pts))
        self.assertEqual(1, len(pts))
        self.assertTrue(pts[0].equals(Point(0, 2)))

        # f_relation
        polys = [Point(0, 2).buffer(1), Point(0, 100).buffer(1)]
        polys = list(filter(polygon.ext.f_relation().intersects(), polys))
        self.assertEqual(1, len(polys))
        self.assertTrue(Point(0, 2).buffer(1).equals(polys[0]))

        # f_alignment
        alignments = [LineString([(0, 0), (1, -1)]),
                      LineString([(0, 0), (1, 0)])]
        result = list(filter(polygon.ext.f_alignment().alignable(), alignments))
        self.assertEqual(1, len(result))

        result = list(filter(polygon.ext.f_alignment(angle_tol=46).alignable(), alignments))
        self.assertEqual(2, len(result))

        # f_angle
        polys = [Point(2, 2).buffer(0.5), Point(2, 2).buffer(3)]
        result = list(filter(polygon.ext.f_angle().angle_range_relation(10, 10).contains(), polys))
        self.assertEqual(1, len(result))

        # almost_intersects
        self.assertTrue(polygon.ext.almost_intersects(Point(0, 2.000001), dist_tol=0.001))
        self.assertFalse(polygon.ext.almost_intersects(Point(0, 2.000001), dist_tol=0.00000001))
