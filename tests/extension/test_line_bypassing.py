from unittest import TestCase

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.coord import Coord
from shapely.extension.util.line_bypassing import LineBypassing
from shapely.geometry import LineString, box
from shapely.wkt import loads


class LineBypassingTest(TestCase):
    def test_bypass_in_simple_case(self):
        line = LineString([(0, 0), (100, 0)])
        poly = box(5, -1, 15, 10)
        short_bypassing = LineBypassing(line).bypass(poly)
        self.assertTrue(isinstance(short_bypassing, LineString))
        self.assertTrue(short_bypassing.length > line.length)
        self.assertFalse(short_bypassing.intersects(poly.buffer(-MATH_EPS)))
        self.assertTrue(Coord.dist(short_bypassing.coords[0], line.coords[0]) < MATH_EPS)
        self.assertTrue(Coord.dist(short_bypassing.coords[-1], line.coords[-1]) < MATH_EPS)

        long_bypassing = LineBypassing(line).bypass(poly, chosen_longer_path=True)
        self.assertTrue(isinstance(long_bypassing, LineString))
        self.assertTrue(long_bypassing.length > line.length)
        self.assertFalse(long_bypassing.intersects(poly.buffer(-MATH_EPS)))
        self.assertTrue(Coord.dist(long_bypassing.coords[0], line.coords[0]) < MATH_EPS)
        self.assertTrue(Coord.dist(long_bypassing.coords[-1], line.coords[-1]) < MATH_EPS)

        self.assertTrue(short_bypassing.length < long_bypassing.length)

    def test_bypass_for_case0(self):
        poly = loads('POLYGON ((40 26, 32 23, 30 14, 50.5 8.6, 56 15, 46 20, 40 20, 43 24, 40 26))')
        line = loads(
            'LINESTRING (57 27, 56.1 26.1, 55.1 25.6, 53.9 24.7, 52.4 23.6, 51.6 22.9, 50.6 21.9, 49.2 20.3, 48.3 19.4, 47.5 18.6, 46.7 17.7, 45.9 16.7, 45.1 15.6, 44.3 14.4, 43.8 13.4, 43.3 12.4, 42.9 11.1, 42.7 10.1, 42.4 8.2, 43 4.5, 43.3 3.1, 43.7 2.1, 44.3 1.2, 44.9 0.4, 48 -2)')
        short_bypassing = LineBypassing(line).bypass(poly)
        self.assertTrue(isinstance(short_bypassing, LineString))
        self.assertTrue(short_bypassing.length > line.length)
        self.assertFalse(short_bypassing.intersects(poly.buffer(-MATH_EPS)))
        self.assertTrue(Coord.dist(short_bypassing.coords[0], line.coords[0]) < MATH_EPS)
        self.assertTrue(Coord.dist(short_bypassing.coords[-1], line.coords[-1]) < MATH_EPS)

        long_bypassing = LineBypassing(line).bypass(poly, chosen_longer_path=True)
        self.assertTrue(isinstance(long_bypassing, LineString))
        self.assertTrue(long_bypassing.length > line.length)
        self.assertFalse(long_bypassing.intersects(poly.buffer(-MATH_EPS)))
        self.assertTrue(Coord.dist(long_bypassing.coords[0], line.coords[0]) < MATH_EPS)
        self.assertTrue(Coord.dist(long_bypassing.coords[-1], line.coords[-1]) < MATH_EPS)

        self.assertTrue(short_bypassing.length < long_bypassing.length)

    def test_bypass_multipoly(self):
        multipoly = loads(
            'MULTIPOLYGON (((2.1 7.9, 0.8 7.5, 0.8 6.3, 1.9 5.4, 2.9 5.6, 2.5 6.3, 4.2 6.5, 4.2 7.9, 2.1 7.9)), ((5.9 4.5, 4.7 4.5, 4.7 3.6, 3.5 3.5, 3.7 2.3, 6 2.3, 6 3.2, 5.9 4.5)))')
        line = loads('LINESTRING (1.2 8.3, 1.1 5.5, 3.5 6, 4.1 1.7, 5.2 1.7, 6.3 3.4)')
        short_bypassing = LineBypassing(line).bypass(multipoly)
        self.assertTrue(isinstance(short_bypassing, LineString))
        self.assertTrue(short_bypassing.length > line.length)
        self.assertFalse(short_bypassing.intersects(multipoly.buffer(-MATH_EPS)))
        self.assertTrue(Coord.dist(short_bypassing.coords[0], line.coords[0]) < MATH_EPS)
        self.assertTrue(Coord.dist(short_bypassing.coords[-1], line.coords[-1]) < MATH_EPS)

    def test_bypass_disjoint_poly(self):
        line = LineString([(0, 0), (100, 0)])
        poly = box(1, 1, 2, 2)
        short_bypassing = LineBypassing(line).bypass(poly)
        self.assertTrue(line.almost_equals(short_bypassing))
