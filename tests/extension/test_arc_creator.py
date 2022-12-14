from unittest import TestCase

from shapely.extension.util.arc_creator import FixedRadiusArcCreator
from shapely.geometry import Point, LineString
from shapely.wkt import loads


class FixedRadiusArcCreatorTest(TestCase):
    def test_create_arcs_by_2_points(self):
        with self.assertRaises(RuntimeError):
            FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(Point(10, 0))

        result = FixedRadiusArcCreator(1).intersects_with(Point(0, 0)).intersects_with(Point(2, 0)).create_arcs()
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
                  .intersects_with(Point(0, 6)).create_arcs())
        self.assertEqual(3, len(result))
        self.assertTrue(Point(-6, 6).almost_equals(result[0]._center))
        self.assertTrue(Point(6, 6).almost_equals(result[1]._center))
        self.assertTrue(Point(6, 6).almost_equals(result[2]._center))

    def test_arcs_returned_given_2_perpendicular_lines(self):
        line0 = LineString([(0, 0), (10, 0)])
        line1 = LineString([(0, 0), (0, 10)])

        creator = FixedRadiusArcCreator(2.5)
        creator = creator.intersects_with(line1, dist_tol=1e-2).intersects_with(line0, dist_tol=1e-2)
        arcs = creator.create_arcs()
        self.assertEqual(4, len(arcs))

