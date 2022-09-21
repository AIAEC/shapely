from unittest import TestCase

from shapely.extension.predicator.relation_predicator_creator import RelationPredicatorCreator
from shapely.geometry import box


class RelationPredicatorCreatorTest(TestCase):
    def test_intersects(self):
        predicator = RelationPredicatorCreator(box(0, 0, 1, 1)).intersects(component_buffer=1e-3)
        self.assertTrue(predicator(box(1, 0, 2, 1)))
        self.assertFalse(predicator(box(1.1, 0, 2, 1)))
