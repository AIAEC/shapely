from _operator import attrgetter
from unittest import TestCase

from shapely.extension.strategy.decompose_strategy import DefaultDecomposeStrategy, CurveDecomposeStrategy
from shapely.geometry import Polygon, MultiPoint, Point, LineString, box, GeometryCollection, MultiPolygon, \
    MultiLineString


class DecomposeStrategyTest(TestCase):
    def test_handler(self):
        strategy = DefaultDecomposeStrategy()
        self.assertEqual(strategy.handler(Polygon([(0, 0), (1, 0), (1, 1)])), strategy.polygon_to_multilinestring)
        self.assertEqual(strategy.handler([MultiPoint([Point(0, 0)])]), strategy.multipoint_to_point)
        self.assertEqual(strategy.handler(1), strategy.empty_handler)

    def test_can_be_handled_checker(self):
        strategy = DefaultDecomposeStrategy()
        self.assertFalse(strategy.can_be_handled(1))
        self.assertTrue(strategy.can_be_handled(LineString([(0, 0), (1, 1)])))
        self.assertFalse(strategy.can_be_handled(Point(0, 0)))

    def test_type_of(self):
        self.assertEqual(Point, DefaultDecomposeStrategy.type_of(Point(0, 0)))
        self.assertEqual(Polygon, DefaultDecomposeStrategy.type_of(box(0, 0, 1, 1)))
        self.assertEqual(Point, DefaultDecomposeStrategy.type_of([Point(0, 0), Point(1, 1)]))
        self.assertIsNone(DefaultDecomposeStrategy.type_of([]))

    def test_decomposing_index(self):
        self.assertTrue(
            DefaultDecomposeStrategy.decomposing_index(GeometryCollection) < DefaultDecomposeStrategy.decomposing_index(
                Point))
        self.assertTrue(
            DefaultDecomposeStrategy.decomposing_index(Point) < DefaultDecomposeStrategy.decomposing_index(None))

    def test_multipolygon_to_polygons(self):
        strategy = DefaultDecomposeStrategy()
        multi_poly = MultiPolygon([box(0, 0, 1, 1), box(1, 1, 2, 2)])
        self.assertTrue(all(isinstance(geom, Polygon) for geom in strategy.multipolygon_to_polygons(multi_poly)))
        self.assertTrue(all(isinstance(geom, Polygon) for geom in strategy.multipolygon_to_polygons([multi_poly])))
        self.assertEqual(2, len(strategy.multipolygon_to_polygons([multi_poly])))

    def test_polygon_to_multilinestring(self):
        strategy = DefaultDecomposeStrategy()
        poly = box(0, 0, 1, 1)
        self.assertTrue(all(isinstance(geom, MultiLineString) for geom in strategy.polygon_to_multilinestring(poly)))
        self.assertTrue(all(isinstance(geom, MultiLineString) for geom in strategy.polygon_to_multilinestring([poly])))
        self.assertEqual(1, len(strategy.polygon_to_multilinestring([poly])))
        self.assertAlmostEqual(4, sum(map(attrgetter('length'), strategy.polygon_to_multilinestring(poly))))

    def test_multilinestring_to_linestring(self):
        strategy = DefaultDecomposeStrategy()
        multilinestring = MultiLineString([LineString([(0, 0), (1, 1)])])
        self.assertTrue(
            all(isinstance(geom, LineString) for geom in strategy.multilinestring_to_linestring(multilinestring)))
        self.assertTrue(
            all(isinstance(geom, LineString) for geom in strategy.multilinestring_to_linestring([multilinestring])))
        self.assertEqual(1, len(strategy.multilinestring_to_linestring([multilinestring])))

    def test_linestring_to_multipoint(self):
        strategy = DefaultDecomposeStrategy()
        linestring = LineString([(0, 0), (1, 1)])
        self.assertTrue(all(isinstance(geom, MultiPoint) for geom in strategy.segment_to_multipoint(linestring)))
        self.assertTrue(all(isinstance(geom, MultiPoint) for geom in strategy.segment_to_multipoint([linestring])))
        self.assertEqual(1, len(strategy.segment_to_multipoint([linestring])))

    def test_multipoint_to_point(self):
        strategy = DefaultDecomposeStrategy()
        multipoint = MultiPoint([Point(0, 0), Point(1, 1)])
        self.assertTrue(all(isinstance(geom, Point) for geom in strategy.multipoint_to_point(multipoint)))
        self.assertTrue(all(isinstance(geom, Point) for geom in strategy.multipoint_to_point([multipoint])))
        self.assertEqual(2, len(strategy.multipoint_to_point([multipoint])))


class CurveDecomposeStrategyTest(TestCase):
    def test_multilinestring_to_linestring(self):
        strategy = CurveDecomposeStrategy(45)
        input = MultiLineString([Point(0, 0).buffer(10).exterior])
        result = strategy.multilinestring_to_linestring(input)
        self.assertEqual(1, len(result))

        input = MultiLineString([box(0, 0, 1, 1).exterior])
        result = strategy.multilinestring_to_linestring(input)
        self.assertEqual(4, len(result))

        input = MultiLineString([LineString([(0, 0), (1, 0), (2, 0.1)])])
        result = strategy.multilinestring_to_linestring(input)
        self.assertEqual(1, len(result))
