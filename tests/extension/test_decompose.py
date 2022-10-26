from unittest import TestCase

from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.util.decompose import decompose
from shapely.geometry import MultiPolygon, box, Point, LineString, GeometryCollection, MultiPoint, Polygon, \
    LinearRing


class DecomposeTest(TestCase):
    def test_decompose_multipolygon_to_point(self):
        multipolygon = MultiPolygon([box(0, 0, 1, 1), box(1, 1, 2, 2)])
        points = decompose(multipolygon, target_class=Point)
        self.assertTrue(all(isinstance(geom, Point) for geom in points))
        self.assertEqual(7, len(points))

    def test_decompose_multipolygon_to_linestring(self):
        multipolygon = MultiPolygon([box(0, 0, 1, 1), box(1, 1, 2, 2)])
        lines = decompose(multipolygon, target_class=LineString)
        self.assertTrue(all(isinstance(geom, LineString) for geom in lines))
        self.assertEqual(2, len(lines))

    def test_decompose_geometry_collection_to_point(self):
        geom_col = GeometryCollection([MultiPolygon([box(0, 0, 1, 1), box(1, 1, 2, 2)]),
                                       Point(0, 1),
                                       LineString([(1, 1), (2, 2)])])
        points = decompose(geom_col, target_class=Point)

        self.assertTrue(all(isinstance(geom, Point) for geom in points))
        self.assertEqual(10, len(points))

    def test_falsy_case_of_decomposing_multipoint_to_polygon(self):
        multipoint = MultiPoint([Point(0, 0), Point(1, 1)])
        result = decompose(multipoint, target_class=Polygon)
        self.assertTrue(isinstance(result, list))
        self.assertEqual(1, len(result))
        self.assertTrue(multipoint.equals(result[0]))

    def test_decompose_linestring_to_segment(self):
        linestring = LineString([(0, 0), (1, 1), (2, 1), (2, 3), (5, 3)])
        segments = linestring.ext.decompose(StraightSegment).to_list()
        self.assertEqual(len(segments), 4)

        linearring = LinearRing([(0, 0), (1, 1), (2, 1), (2, 3), (5, 3), (5, 0), (0, 0)])
        segments = linearring.ext.decompose(StraightSegment).to_list()
        self.assertEqual(len(segments), 6)
