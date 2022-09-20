from unittest import TestCase

from shapely.extension.geometry.rect import Rect


class RectTest(TestCase):
    def test_create_rect(self):
        try:
            Rect([(0, 0), (1, 0), (1, 1), (0, 1)])
        except:
            self.fail()

        with self.assertRaises(ValueError):
            Rect([(0, 0), (1, 0), (1, 1)])

    def test_angle(self):
        self.assertEqual(45, Rect([(0, 0), (2, 2), (1, 3), (-1, 1)]).angle)
