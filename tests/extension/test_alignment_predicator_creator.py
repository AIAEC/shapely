from unittest import TestCase

from shapely.extension.predicator.alignment_predicator_creator import AlignmentPredicatorCreator
from shapely.geometry import box, Polygon, LineString


class AlignmentPredicatorCreatorTest(TestCase):
    def test_alignable_positive_cases(self):
        alignment = AlignmentPredicatorCreator(box(0, 0, 1, 1))
        self.assertTrue(alignment.alignable()(box(2, 2, 3, 3)))
        self.assertTrue(alignment.alignable()(LineString([(0, -10), (10, -10)])))
        self.assertTrue(alignment.alignable()(LineString([(-10, -1), (-10, 2)])))

        alignment = AlignmentPredicatorCreator(Polygon([(0, 0), (1, 1), (0, 2), (-1, 1)]))
        self.assertTrue(alignment.alignable()(LineString([(0, -10), (10, 0)])))

    def test_alignable_negative_cases(self):
        alignment = AlignmentPredicatorCreator(box(0, 0, 1, 1))
        self.assertFalse(alignment.alignable()(Polygon([(0, 0), (1, 1), (0, 2), (-1, 1)])))

    def test_shortest_distance_predicator(self):
        alignment = AlignmentPredicatorCreator(Polygon([(0, 0), (1, 1), (0, 2), (-1, 1)]))
        self.assertTrue(alignment.shortest_distance().less_than(1)(LineString([(0, -1), (1, 0)])))

        predicator = (0.5 < alignment.shortest_distance()) & (alignment.shortest_distance() < 1)
        self.assertTrue(predicator(LineString([(0, -1), (1, 0)])))
        self.assertFalse(predicator(LineString([(0, -2), (2, 0)])))
