from math import sqrt, isclose
from unittest import TestCase

from shapely.extension.model.coord import Coord
from shapely.geometry import Point


class CoordTest(TestCase):
    def test_coord_dist(self):
        coord0 = (0, 0)
        coord1 = (1, 1)
        self.assertAlmostEqual(sqrt(2), Coord.dist(coord0, coord1))

    def test_coord_angle(self):
        coord0 = (0, 0)
        coord1 = (1, 1)
        self.assertAlmostEqual(45, Coord.angle(coord0, coord1).degree)

    def test_including_angles(self):
        coords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        result = Coord.including_angles(coords)
        self.assertEqual(2, len(result))
        self.assertTrue(all(isclose(angle.degree, 90) for angle in result))

        result = Coord.including_angles(coords, head_cycling=True, tail_cycling=True)
        self.assertEqual(6, len(result))
        self.assertTrue(all(isclose(angle.degree, 90) for angle in result))

    def test_create_point(self):
        coord = Coord(0, 0)
        try:
            self.assertTrue(Point(coord).equals(Point(0, 0)))
        except:
            self.fail()
