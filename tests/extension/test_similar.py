from unittest import TestCase

from shapely.affinity import rotate
from shapely.extension.util.similar import similar
from shapely.geometry import box, Polygon, LineString, Point, GeometryCollection, MultiPoint, MultiLineString, \
    MultiPolygon


class SimilarTest(TestCase):
    def test_polygons_similarity(self):
        polygon = box(0, 0, 10, 5)
        similar_polygon = Polygon([(-1e-5, -1e-5), (10 + 1e-4, 0), (10, 5), (0, 5)])
        self.assertTrue(similar(polygon, similar_polygon, 1e-2))

        non_similar_polygon = rotate(polygon, 30)
        self.assertFalse(similar(polygon, non_similar_polygon))

    def test_linestring_similarity(self):
        line = LineString([(256, 135), (0, 0)])
        similar_line = LineString([(256.0001, 134.99999), (1e-6, 1e-4)])
        self.assertTrue(similar(line, similar_line, 1e-3))
        similar_line = rotate(line, 1e-3)
        self.assertTrue(similar(line, similar_line, 1e-1))

    def test_different_type_similarity(self):
        line = LineString([(0, 0), (1, 0)])
        point = Point(0, 1)
        self.assertFalse(similar(line, point))
        self.assertFalse(similar(point, line))

    def test_empty_geoms_similarity(self):
        line = LineString()
        point = Point()
        self.assertTrue(similar(line, point))

        geom_col = GeometryCollection()
        self.assertTrue(similar(geom_col, point))
        self.assertTrue(similar(geom_col, line))

    def test_similarity_of_geom_and_multi_geom(self):
        point = Point(0, 0)
        multi_point = MultiPoint([point])
        self.assertTrue(similar(point, multi_point))

        multi_point = MultiPoint([Point(1, 0)])
        self.assertFalse(similar(point, multi_point))

        line = LineString([(0, 0), (1, 0)])
        multi_line = MultiLineString([line])
        self.assertTrue(similar(line, multi_line))

        poly = box(0, 0, 1, 1)
        multi_poly = MultiPolygon([poly])
        self.assertTrue(similar(poly, multi_poly))

        self.assertFalse(similar(point, None))
        self.assertFalse(similar(1, point))

        self.assertFalse(similar(multi_point, GeometryCollection([point])))

    def test_similar_of_geometry_collections(self):
        geom_col0 = GeometryCollection([Point(1, 0), LineString([(1, 0), (1, 1)])])
        geom_col1 = GeometryCollection([Point(0, 0), LineString([(0, 0), (0, 1)])])
        self.assertTrue(similar(geom_col0, geom_col1, area_diff_tol=1.1))
        self.assertFalse(similar(geom_col0, geom_col1, area_diff_tol=0.1))
