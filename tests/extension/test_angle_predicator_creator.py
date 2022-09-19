from unittest import TestCase

from shapely.extension.model.angle import Angle
from shapely.extension.predicator.angle_predicator_creator import AnglePredicatorCreator, AngleRangePredicator
from shapely.geometry import LineString, box, Point


class AngleRangePredicatorTest(TestCase):
    def test_intersects(self):
        self.assertTrue(AngleRangePredicator(45, 45, 45).intersects()(box(1, 1, 2, 2)))
        self.assertFalse(AngleRangePredicator(45, 10, 10).intersects()(box(-2, -2, -1, -1)))

    def test_touches(self):
        self.assertTrue(AngleRangePredicator(45, 45, 45).touches()(box(0, -1, 1, 0)))
        self.assertTrue(AngleRangePredicator(45, 45, 45).touches(abs_tol=0.1)(box(0, -1, 1, -0.00001)))

    def test_contains(self):
        self.assertTrue(AngleRangePredicator(45, 45, 45).contains()(box(1, 1, 2, 2)))
        self.assertFalse(AngleRangePredicator(45, 5, 5).contains()(box(0, 0, 1, 1)))

    def test_contains_angle(self):
        self.assertTrue(AngleRangePredicator(45, 1, 1).contains_angle()(45))
        self.assertTrue(AngleRangePredicator(45, 1, 1).contains_angle()(Angle(45)))
        self.assertTrue(AngleRangePredicator(45, 1, 1).contains_angle()(46))
        self.assertFalse(AngleRangePredicator(45, 1, 1).contains_angle()(47))
        self.assertFalse(AngleRangePredicator(45, 1, 1).contains_angle()(43))


class AnglePredicatorCreatorTest(TestCase):
    def test_geom_angle_predicator(self):
        predicator = (AnglePredicatorCreator(LineString([(0, 0), (1, 1)]))
                      .angle_range_relation(cw_range=10, ccw_range=10)
                      .contains())
        self.assertTrue(predicator(LineString([(0, 0), (1, 1.01)])))
        self.assertTrue(predicator(LineString([(0, 0), (1, 0.99)])))
        self.assertTrue(predicator(Point(100, 100).buffer(1)))

        self.assertFalse(predicator(LineString([(0, 0), (1, 3)])))
        self.assertFalse(predicator(LineString([(0, 0), (1, -1)])))

        predicator = (AnglePredicatorCreator(LineString([(0, 0), (1, 1)]))
                      .angle_range_relation(cw_range=10, ccw_range=10)
                      .contains_angle())
        self.assertTrue(predicator(Angle(45)))
        self.assertFalse(predicator(Angle(60)))

    def test_including_angle(self):
        predicator = (AnglePredicatorCreator(LineString([(0, 0), (1, 1)])).including_angle() < 10)
        self.assertTrue(predicator(LineString([(0, 0), (100, 101)])))
        self.assertFalse(predicator(LineString([(0, 0), (100, 0)])))

        predicator = (AnglePredicatorCreator(LineString([(0, 0), (1, 1)])).including_angle() > 10)
        self.assertFalse(predicator(LineString([(0, 0), (100, 101)])))
        self.assertTrue(predicator(LineString([(0, 0), (100, 0)])))
