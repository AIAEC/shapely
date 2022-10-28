from copy import deepcopy
from unittest import TestCase

from shapely.extension.geometry import StraightSegment


class StraightSegmentTest(TestCase):
    def test_create(self):
        with self.assertRaises(ValueError):
            StraightSegment([(0, 0), (1, 1), (2, 2)])

        line0 = StraightSegment()
        self.assertTrue(line0.is_empty)

        line1 = StraightSegment([(0, 0), (0, 0)])
        self.assertFalse(line1.is_empty)

        line2 = StraightSegment([(0, 0), (0, 1)])
        self.assertTrue(line2.length == 1)

        line3 = deepcopy(line2)
        self.assertEqual(line2, line3)

