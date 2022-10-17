from collections import deque
from unittest import TestCase

from shapely.extension.util.flatten import flatten
from shapely.geometry import Point, LineString, MultiLineString, GeometryCollection, box, MultiPolygon, Polygon


class TestFlatten(TestCase):
    def test_flatten_single_geom(self):
        point = Point(0, 0)
        result = flatten(point).to_list()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].equals(Point(0, 0)))

    def test_flatten_sequence_of_geom(self):
        lines = deque([MultiLineString([LineString([(0, 0), (1, 0)]), LineString([(0, 0), (0, 1)])])])
        result = flatten(lines).to_list()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(2, len(result))
        self.assertTrue(LineString([(0, 0), (1, 0)]).equals(result[0]))
        self.assertTrue(LineString([(0, 0), (0, 1)]).equals(result[1]))

    def test_flatten_nested_geometry_collection(self):
        collection = GeometryCollection([
            GeometryCollection([Point(0, 0), LineString([(1, 0), (1, 1)])]),
            GeometryCollection([box(0, 0, 1, 1)]),
            MultiPolygon([box(1, 1, 2, 2)]),
        ])
        result = flatten(collection).to_list()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(4, len(result))

        result = flatten(collection, Point).to_list()
        self.assertEqual(1, len(result))

        result = flatten(collection, lambda g: g.area > 0).to_list()
        self.assertEqual(2, len(result))
        self.assertTrue(all(isinstance(g, Polygon) for g in result))

    def test_flatten_with_validate(self):
        polygon = Polygon([(0, 0), (10, 0), (8, -5), (3, 5)])
        result = flatten(polygon, validate=True).to_list()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(2, len(result))
        self.assertTrue(all(isinstance(g, Polygon) for g in result))

    def test_flatten_with_filter_empty(self):
        polygon = box(0, 0, 1, 1)
        result = flatten([polygon, Polygon()], filter_out_empty=True).to_list()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].equals(box(0, 0, 1, 1)))

    def test_flatten_polygons_with_holes(self):
        polys = [
            Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                    [[(1, 1), (2, 1), (2, 2), (1, 2)]])
        ]
        result = flatten(polys, Polygon).to_list()
        self.assertEqual(1, len(result))
        self.assertTrue(result[0].equals(polys[0]))