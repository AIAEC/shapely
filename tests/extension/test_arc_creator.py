from unittest import TestCase

from shapely.extension.util.arc_creator import FixedRadiusArcCreator
from shapely.geometry import Point, LineString
from shapely.wkt import loads


class FixedRadiusArcCreatorTest(TestCase):
    def test_create_arcs_by_2_points(self):


        result = FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(Point(2, 0)).create_arcs()
        self.assertEqual(2, len(result))
        self.assertTrue(Point(1, 0).almost_equals(result[0].centroid))
        self.assertAlmostEqual(1, result[0].radius)

        result = (FixedRadiusArcCreator(1)
                  .intersects_with(Point(0, 0))
                  .intersects_with(Point(2, 0))
                  .create_arcs(touched_every_geoms=True))
        self.assertEqual(2, len(result))
        self.assertTrue(Point(1, 0).almost_equals(result[0].centroid))
        self.assertAlmostEqual(1, result[0].radius)

    def test_create_arcs_by_1_point_and_1_line(self):
        line = loads('LINESTRING (-38.89215195971408 -37.61474943371004, -27.390086445156353 -66.16137213520415)')
        point = loads('POINT (-28.99009146070061 -66.80604953533012)')
        result = (FixedRadiusArcCreator(6)
                  .intersects_with(line)
                  .intersects_with(point).create_arcs())
        self.assertEqual(3, len(result))

        result = (FixedRadiusArcCreator(6)
                  .intersects_with(LineString([(0, 0), (10, 0)]))
                  .intersects_with(Point(0, 6))
                  .create_arcs())
        self.assertEqual(3, len(result))
        self.assertTrue(Point(-6, 6).almost_equals(result[0]._center))
        self.assertTrue(Point(6, 6).almost_equals(result[1]._center))
        self.assertTrue(Point(6, 6).almost_equals(result[2]._center))

        result = (FixedRadiusArcCreator(6)
                  .intersects_with(LineString([(0, 0), (10, 0)]))
                  .intersects_with(Point(0, 6))
                  .create_arcs(touched_every_geoms=True))
        self.assertEqual(2, len(result))
        self.assertTrue(Point(6, 6).almost_equals(result[0]._center))
        self.assertTrue(Point(6, 6).almost_equals(result[1]._center))

    def test_arcs_returned_given_2_perpendicular_lines(self):
        line0 = LineString([(0, 0), (10, 0)])
        line1 = LineString([(0, 0), (0, 10)])

        arcs = (FixedRadiusArcCreator(2.5)
                .intersects_with(line1, dist_tol=1e-2)
                .intersects_with(line0, dist_tol=1e-2)
                .create_arcs())
        self.assertEqual(4, len(arcs))

        arcs = (FixedRadiusArcCreator(2.5)
                .intersects_with(line1, dist_tol=1e-2)
                .intersects_with(line0, dist_tol=1e-2)
                .create_arcs(touched_every_geoms=True))
        self.assertEqual(2, len(arcs))

    def test_real_case(self):
        line0 = loads('LINESTRING (-73.1837460895258 -35.81606622708422, -73.39921442697728 24.642203905834293)')
        line1 = loads('LINESTRING (-73.2786930956943 -9.174881655531589, -28.217091449089548 -9.174881655531589)')
        arcs = (FixedRadiusArcCreator(6, angle_step=16)
                .intersects_with(line0)
                .intersects_with(line1)
                .create_arcs())
        self.assertTrue(len(arcs) == 6)
        self.assertTrue(len(list(filter(lambda arc: arc.is_minor_arc, arcs))) == 2)
        self.assertTrue(len(list(filter(lambda arc: arc.is_prior_arc, arcs))) == 4)
