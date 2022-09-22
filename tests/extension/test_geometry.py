from unittest import TestCase

from shapely.geometry import box, Point, LineString, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection


class GeometryTest(TestCase):
    def test_hash(self):
        poly = box(0, 0, 1, 1)
        set_ = {poly, poly}
        self.assertEqual(1, len(set_))

        point = Point(0, 0)
        set_ = {point, point}
        self.assertEqual(1, len(set_))

        line = poly.exterior
        set_ = {line, line}
        self.assertEqual(1, len(set_))

        multi_point = MultiPoint([Point(0, 0), Point(1, 1)])
        set_ = {multi_point, multi_point}
        self.assertEqual(1, len(set_))

        multi_line = MultiLineString([LineString([(0, 0), (1, 1)]), poly.exterior])
        set_ = {multi_line, multi_line}
        self.assertEqual(1, len(set_))

        multi_poly = MultiPolygon([poly, poly])
        set_ = {multi_poly, multi_poly}
        self.assertEqual(1, len(set_))

        geom_col = GeometryCollection([poly, point, line, multi_poly, multi_line, multi_point])
        set_ = {geom_col, geom_col}
        self.assertEqual(1, len(set_))
