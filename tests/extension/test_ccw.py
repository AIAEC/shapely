from unittest import TestCase

from shapely.extension.util.ccw import ccw
from shapely.geometry import Point, LineString, LinearRing, Polygon, GeometryCollection


class CcwTest(TestCase):
    def test_ccw_of_point(self):
        point = Point(0, 0)
        result = ccw(point)
        self.assertTrue(result.equals(point))

    def test_ccw_of_linestring(self):
        line = LineString([(0, 0), (1, 0)])
        result = ccw(line)
        self.assertTrue(result.equals(line))

        ring = LinearRing([(0, 0), (0, 1), (1, 0)])
        result = ccw(ring)
        self.assertTrue(result.equals(LinearRing([(1, 0), (0, 1), (0, 0)])))

        ring = LineString([(0, 0), (1, 0), (0, 1), (0, 0)])
        result = ccw(ring)
        self.assertTrue(result.equals(LineString([(0, 0), (0, 1), (1, 0), (0, 0)])))

    def test_ccw_of_polygon(self):
        poly = Polygon(shell=[(0, 0), (0, 10), (10, 10), (10, 0)],
                       holes=[
                           [(1, 1), (2, 1), (2, 2), (1, 2)],
                           [(2, 2), (3, 2), (3, 3), (2, 3)]
                       ])
        result = ccw(poly)
        expect = Polygon(shell=[(10, 0), (10, 10), (0, 10), (0, 0)],
                         holes=[
                             [(1, 2), (2, 2), (2, 1), (1, 1)],
                             [(2, 3), (3, 3), (3, 2), (2, 2)]
                         ])
        self.assertTrue(result.equals(expect))

    def test_ccw_of_geom_collecton(self):
        collection = GeometryCollection([
            Polygon(shell=[(0, 0), (0, 10), (10, 10), (10, 0)],
                    holes=[
                        [(1, 1), (2, 1), (2, 2), (1, 2)],
                        [(2, 2), (3, 2), (3, 3), (2, 3)]
                    ]),
            LineString([(0, 0), (0, 1), (1, 0), (0, 0)])
        ])

        result = ccw(collection)
        self.assertTrue(isinstance(result, GeometryCollection))
        for geom in result.geoms:
            if isinstance(geom, Polygon):
                expect = Polygon(shell=[(10, 0), (10, 10), (0, 10), (0, 0)],
                                 holes=[
                                     [(1, 2), (2, 2), (2, 1), (1, 1)],
                                     [(2, 3), (3, 3), (3, 2), (2, 2)]
                                 ])
                self.assertTrue(geom.equals(expect))
            else:
                self.assertTrue(geom.equals(LineString([(0, 0), (1, 0), (0, 1), (0, 0)])))
