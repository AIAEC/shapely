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

        result = list(
            {Point(0, 1), Point(0, 1 + 1e-6), LineString([(0, 0), (1, 1)]), box(0, 0, 1, 1), box(0, 0, 1, 1 + 1e-6)})
        self.assertEqual(5, len(result))

        result = list(
            {box(0.001, 0.11, 1.11, 2.22), box(0.001, 0.11, 1.11, 2.22), box(0, 0, 1, 1)})
        self.assertEqual(2, len(result))

    def test_cargo(self):
        poly = box(0, 0, 1, 1)
        poly.ext.cargo['proj'] = 1
        self.assertEqual(1, poly.ext.cargo['proj'])

        poly = box(0, 0, 1, 1)
        self.assertDictEqual({}, poly.ext.cargo)
        poly.ext.cargo['proj'] = 2
        self.assertEqual(2, poly.ext.cargo['proj'])

        point = Point(0, 0)
        point.ext.cargo[0] = 1
        self.assertEqual(1, point.ext.cargo[0])

        geom_col = GeometryCollection([Point(0, 0), poly])
        self.assertDictEqual({}, geom_col.ext.cargo)
        geom_col.ext.cargo[0] = 0
        self.assertEqual(0, geom_col.ext.cargo[0])
