from unittest import TestCase

from shapely import wkt
from shapely.extension.constant import MATH_EPS, COMPARE_EPS
from shapely.extension.geometry.empty import EMPTY_GEOM
from shapely.extension.model.vector import Vector
from shapely.geometry import box, LineString, Polygon, Point
from shapely.ops import nearest_points
from shapely.wkt import loads


class PolygonExtensionTest(TestCase):
    def test_edge_pair_with(self):
        polygon = box(0, 0, 1, 1)
        self.assertEqual(4, len(list(polygon.ext.edge_pair_with(LineString([(0, 0), (1, 0)])))))

    def test_union(self):
        polygon = box(0, 0, 1, 1)
        large_poly = box(2, -10, 100, 100)
        result = polygon.ext.union(large_poly, direction=Vector(1, 1), dist_tol=2)
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.area > polygon.area + large_poly.area)

    def test_union_without_direction(self):
        polygon0 = loads('POLYGON ((3 8, 5 8, 5 6, 3 6, 3 8))')
        polygon1 = loads('POLYGON ((0 8, 2 10, 3 9, 1 7, 0 8))')
        result = polygon0.ext.union(polygon1, dist_tol=2)
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.area > polygon0.area + polygon1.area)

    def test_cut_not_intersect(self):
        poly1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
        point1 = Point(0, 0)
        vector1 = Vector(1, 1)
        result1 = poly1.ext.cut(point1, vector1, 2.5)
        self.assertLessEqual(abs(result1.area - 2.5), MATH_EPS)

        self.assertTrue(poly1.ext.cut(Point(-1, -1), Vector(-1, -1), 2.5).equals(EMPTY_GEOM))
        self.assertTrue(poly1.ext.cut(Point(-100, -100), Vector(1, 1), 2.5).equals(EMPTY_GEOM))

        poly2 = wkt.loads("POLYGON ((-40 20, -10 20, -10 10, -40 10, -40 20))")
        point2 = Point(0, 0)
        vector2 = Vector(-1, 1)
        result2 = poly2.ext.cut(point2, vector2, 150)
        expect2 = wkt.loads("POLYGON ((-30 10, -20 20, -10 20, -10 10, -30 10))")
        self.assertTrue(expect2.within(result2.buffer(COMPARE_EPS)))
        self.assertTrue(result2.within(expect2.buffer(COMPARE_EPS)))

        vector3 = Vector(0, 1)
        result3 = poly2.ext.cut(point2, vector3, 150)
        expect3 = wkt.loads("POLYGON ((-40 15, -10 15, -10 10, -40 10, -40 15))")
        self.assertTrue(expect3.within(result3.buffer(COMPARE_EPS)))
        self.assertTrue(result3.within(expect3.buffer(COMPARE_EPS)))

        point4 = Point(0, 30)
        vector4 = Vector(-1, -1)
        result4 = poly2.ext.cut(point4, vector4, 150)
        expect4 = wkt.loads("POLYGON ((-30 20, -10 20, -10 10, -20 10, -30 20))")
        self.assertTrue(expect4.within(result4.buffer(COMPARE_EPS)))
        self.assertTrue(result4.within(expect4.buffer(COMPARE_EPS)))

        vector5 = Vector(0, -1)
        result5 = poly2.ext.cut(point4, vector5, 150)
        expect5 = wkt.loads("POLYGON ((-40 15, -40 20, -10 20, -10 15, -40 15))")
        self.assertTrue(expect5.within(result5.buffer(COMPARE_EPS)))
        self.assertTrue(result5.within(expect5.buffer(COMPARE_EPS)))

        point6 = Point(-50, 30)
        vector6 = Vector(1, -1)
        result6 = poly2.ext.cut(point6, vector6, 150)
        expect6 = wkt.loads("POLYGON ((-30 10, -40 10, -40 20, -20 20, -30 10))")
        self.assertTrue(expect6.within(result6.buffer(COMPARE_EPS)))
        self.assertTrue(result6.within(expect6.buffer(COMPARE_EPS)))

        vector7 = Vector(-1, 0)
        result7 = poly2.ext.cut(point2, vector7, 150)
        expect7 = wkt.loads("POLYGON ((-25 20, -10 20, -10 10, -25 10, -25 20))")
        self.assertTrue(expect7.within(result7.buffer(COMPARE_EPS)))
        self.assertTrue(result7.within(expect7.buffer(COMPARE_EPS)))

        vector8 = Vector(1, 0)
        result8 = poly2.ext.cut(point6, vector8, 150)
        expect8 = wkt.loads("POLYGON ((-25 10, -40 10, -40 20, -25 20, -25 10))")
        self.assertTrue(expect8.within(result8.buffer(COMPARE_EPS)))
        self.assertTrue(result8.within(expect8.buffer(COMPARE_EPS)))

    def test_cut_intersect(self):
        poly1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
        point1 = Point(1, 1)
        vector1 = Vector(1, 1)
        result1 = poly1.ext.cut(point1, vector1, 1.5)
        expect1 = wkt.loads("POLYGON ((0 2, 1 2, 2 1, 2 0, 0 2))")
        self.assertTrue(expect1.within(result1.buffer(COMPARE_EPS)))
        self.assertTrue(result1.within(expect1.buffer(COMPARE_EPS)))

    def test_cut_special_polygon(self):
        poly1 = Polygon([(0, 0), (0, 2), (1, 2), (1, 1), (2, 1), (2, 2), (3, 2), (3, 0), (0, 0)])
        point1 = Point(1.5, -1)
        vector1 = Vector(0, 1)
        result1 = poly1.ext.cut(point1, vector1, 4)
        expect1 = wkt.loads("POLYGON ((1 1.5, 1 1, 2 1, 2 1.5, 3 1.5, 3 0, 0 0, 0 1.5, 1 1.5))")
        self.assertLessEqual(abs(result1.area - 4), MATH_EPS)
        self.assertTrue(expect1.within(result1.buffer(COMPARE_EPS)))
        self.assertTrue(result1.within(expect1.buffer(COMPARE_EPS)))

        point2 = Point(0, 2)
        vector2 = Vector(0, -1)
        result2 = poly1.ext.cut(point2, vector2, 0.5)
        expect2 = wkt.loads("MULTIPOLYGON (((1 2, 1 1.75, 0 1.75, 0 2, 1 2)), ((3 2, 3 1.75, 2 1.75, 2 2, 3 2)))")
        self.assertLessEqual(abs(result2.area - 0.5), MATH_EPS)
        self.assertTrue(expect2.within(result2.buffer(COMPARE_EPS)))
        self.assertTrue(result2.within(expect2.buffer(COMPARE_EPS)))

    def test_convex_points_of_polygon(self):
        # with duplicate coords and concave coords
        poly = Polygon([(0, 0), (2, 0), (2, 2), (1, 2), (1, 1), (0, 1), (0, 1), (0, 1)])
        convex_points = poly.ext.convex_points()
        self.assertEqual(5, len(convex_points))
        self.assertTrue(Point(0, 0) in convex_points)
        self.assertTrue(Point(2, 0) in convex_points)
        self.assertTrue(Point(2, 2) in convex_points)
        self.assertTrue(Point(1, 2) in convex_points)
        self.assertTrue(Point(0, 1) in convex_points)
