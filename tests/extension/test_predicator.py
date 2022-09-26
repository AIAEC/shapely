from dataclasses import dataclass
from operator import attrgetter
from unittest import TestCase

from toolz import identity

from shapely.extension.predicator.predicator import Predicator
from shapely.geometry import Point, box
from shapely.geometry.base import BaseGeometry


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

    def test_attr_getter_param(self):
        def func(geom_obj, attr_getter=identity):
            return attr_getter(geom_obj).area == 0

        predicator = Predicator(func)
        self.assertTrue(predicator(Point(0, 0)))
        self.assertFalse(predicator(box(0, 0, 1, 1)))

        @dataclass
        class Test0:
            shape: BaseGeometry
            other: int

        self.assertTrue(predicator(Test0(Point(0, 0), 1), attrgetter('shape')))
        self.assertFalse(predicator(Test0(box(0, 0, 1, 1), 2), attrgetter('shape')))
