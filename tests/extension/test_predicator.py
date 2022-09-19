from unittest import TestCase

from shapely.extension.predicator.predicator import Predicator
from shapely.geometry import Point, box


class PredicatorTest(TestCase):
    def test_call_predicator(self):
        predicator = Predicator(lambda geom: geom.area == 0)
        self.assertTrue(predicator(Point(0, 0)))
        self.assertFalse(predicator(box(0, 0, 1, 1)))

    def test_composite_predicator(self):
        true_predicator = Predicator(lambda _: True)
        false_predicator = Predicator(lambda _: False)
        self.assertTrue((true_predicator | false_predicator)(None))
        self.assertFalse((true_predicator & false_predicator)(None))
        self.assertTrue(((true_predicator | false_predicator) | (false_predicator & true_predicator))(None))
