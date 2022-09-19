from unittest import TestCase

from shapely.extension.predicator.distance_predicator_creator import DistancePredicatorCreator
from shapely.geometry import box, Point


class DistancePredicatorCreatorTest(TestCase):
    def test_distance_less_than(self):
        predicator = DistancePredicatorCreator(box(0, 0, 1, 1)).less_than(1)
        self.assertTrue(predicator(Point(1.9, 0)))
        self.assertFalse(predicator(Point(2.1, 0)))

    def test_distance_composite_predicator(self):
        creator = DistancePredicatorCreator(box(0, 0, 1, 1))
        predicator = (0.8 < creator) & (creator < 1.2)
        self.assertTrue(predicator(Point(1.9, 0)))
        self.assertTrue(predicator(Point(2.1, 0)))
        self.assertFalse(predicator(Point(1.7, 0)))
        self.assertFalse(predicator(Point(2.3, 0)))
