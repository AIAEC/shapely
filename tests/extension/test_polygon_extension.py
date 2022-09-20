from unittest import TestCase

from shapely.extension.model import Vector
from shapely.extension.strategy.decompose_strategy import StraightSegmentDecomposeStrategy
from shapely.geometry import box, LineString, Polygon


class PolygonExtensionTest(TestCase):
    def test_edge_pair_with(self):
        polygon = box(0, 0, 1, 1)
        self.assertEqual(4, len(list(polygon.ext.edge_pair_with(LineString([(0, 0), (1, 0)]),
                                                                StraightSegmentDecomposeStrategy()))))

    def test_has_edge_parallel_to(self):
        polygon = box(0, 0, 1, 1)
        self.assertTrue(polygon.ext.has_edge_parallel_to(LineString([(0, 0), (1, 0)])))
        self.assertFalse(polygon.ext.has_edge_parallel_to(LineString([(0, 0), (1, 1)])))

    def test_has_edge_perpendicular_to(self):
        polygon = box(0, 0, 1, 1)
        self.assertTrue(polygon.ext.has_edge_perpendicular_to(LineString([(0, 0), (1, 0)])))
        self.assertFalse(polygon.ext.has_edge_perpendicular_to(LineString([(0, 0), (1, 1)])))

    def test_has_edge_collinear_to(self):
        polygon = box(0, 0, 1, 1)
        self.assertTrue(polygon.ext.has_edge_collinear_to(LineString([(0, 0), (1, 0)])))
        self.assertFalse(polygon.ext.has_edge_collinear_to(LineString([(0, 0), (1, 1)])))

    def test_union(self):
        polygon = box(0, 0, 1, 1)
        large_poly = box(2, -10, 100, 100)
        result = polygon.ext.union(large_poly, direction=Vector(1, 1), dist_tol=2)
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.area > polygon.area + large_poly.area)
