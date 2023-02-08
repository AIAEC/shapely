from unittest import TestCase

import pytest

from shapely.extension.util.legalize import legalize
from shapely.geometry import (
    Polygon, MultiPolygon, LineString, GeometryCollection, Point, MultiLineString, MultiPoint, LinearRing)


@pytest.mark.skip("TODO fix it")  # TODO
class TestLegalize(TestCase):
    def test_legalize_polygon(self):
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (1, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
        expect1 = GeometryCollection([Polygon([(1, 0), (0, 0), (0, 2), (2, 2), (2, 0), (1, 0)]),
                                      LineString([(1, 0), (1, 1)])])
        self.assertTrue(legalize(poly1).equals(expect1))

        poly2 = Polygon([(0, 0), (2, 0), (0, 1), (0, 2), (0, 0)])
        expect2 = GeometryCollection([Polygon([(0, 1), (2, 0), (0, 0), (0, 1)]),
                                      LineString([(0, 1), (0, 2)])])
        self.assertTrue(legalize(poly2).equals(expect2))

        poly3 = Polygon([(0, 4), (2, 0), (0, 0), (2, 4), (0, 4)])
        expect3 = MultiPolygon([Polygon([(1, 2), (2, 0), (0, 0), (1, 2)]),
                                Polygon([(1, 2), (0, 4), (2, 4), (1, 2)])])
        self.assertTrue(legalize(poly3).equals(expect3))

    def test_legalize_linestring(self):
        poly1 = LineString([(0, 0), (0, 0), (0, 0), (0, 0)])
        expect1 = Point(0, 0)
        self.assertTrue(legalize(poly1).equals(expect1))

    def test_legalize_linearRing(self):
        ring1 = LinearRing([(0, 0), (1, 0), (1, 0), (2, 0), (0, 0)])
        expect1 = LinearRing([(0, 0), (1, 0), (2, 0), (0, 0)])
        self.assertTrue(legalize(ring1).equals(expect1))

    def test_legalize_multi(self):
        multi_linestring = MultiLineString([LineString([(0, 0), (0, 0)]), LineString([(2, 2), (2, 2)])])
        expect2 = MultiPoint([(0, 0), (2, 2)])
        self.assertTrue(legalize(multi_linestring).equals(expect2))

        multi_polygon = MultiPolygon([Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
                                      Polygon([(1, 0), (2, 0), (2, 1), (1, 1), (1, 0)])])
        expect3 = GeometryCollection([Polygon([(1, 0), (0, 0), (0, 1), (1, 1), (2, 1), (2, 0), (1, 0)]),
                                      LineString([(1, 0), (1, 1)])])
        self.assertTrue(legalize(multi_polygon).equals(expect3))

        geom_collection = GeometryCollection([Polygon([(0, 0), (2, 0), (0, 1), (0, 2), (0, 0)]),
                                              LineString([(3, 0), (3, 0)]),
                                              Point(3, 3)])
        expect4 = GeometryCollection([GeometryCollection([Polygon([(0, 1), (2, 0), (0, 0), (0, 1)]),
                                                          LineString([(0, 1), (0, 2)])]),
                                      Point(3, 0),
                                      Point(3, 3)])
        self.assertTrue(legalize(geom_collection).equals(expect4))
