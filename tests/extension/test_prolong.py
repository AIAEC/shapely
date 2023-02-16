from unittest import TestCase

from shapely.extension.constant import MATH_EPS
from shapely.extension.util.prolong import prolong
from shapely.geometry import LineString
from shapely.wkt import loads


class ProlongTest(TestCase):
    def assert_geometries_almost_equal(self, geom0, geom1, delta=MATH_EPS):
        return geom0.buffer(delta).contains(geom1) and geom1.buffer(MATH_EPS).contains(geom0)

    def test_prolong(self):
        line = LineString([(0, 0), (1, 0), (1, 1)])
        result = prolong(line, front_prolong_len=1, end_prolong_len=1)
        self.assertTrue(isinstance(result, LineString) and result.is_valid)
        self.assert_geometries_almost_equal(LineString([(-1, 0), (1, 0), (1, 2)]), result)
        self.assertEqual(3, len(list(result.coords)))

        line_with_duplicate_coords = LineString([(0, 0), (0, 0), (0, 0), (1, 0), (1, 1), (1, 1)])
        result = prolong(line_with_duplicate_coords, front_prolong_len=1, end_prolong_len=1)
        self.assertTrue(isinstance(result, LineString) and result.is_valid)
        self.assert_geometries_almost_equal(LineString([(-1, 0), (1, 0), (1, 2)]), result)

        empty_line = LineString()
        result = prolong(empty_line, front_prolong_len=1, end_prolong_len=1)
        self.assertTrue(isinstance(result, LineString) and result.is_empty)

        invalid_line = LineString([(0, 0), (0, 0)])
        result = prolong(invalid_line, front_prolong_len=1, end_prolong_len=1)
        self.assertTrue(isinstance(result, LineString) and not result.is_valid)

        straight_line = LineString([(0, 0), (1, 0)])
        result = prolong(straight_line, front_prolong_len=1, end_prolong_len=1)
        self.assert_geometries_almost_equal(LineString([(-1, 0), (2, 0)]), result)
        self.assertEqual(2, len(list(result.coords)))

        float_line = loads(
            'LINESTRING (-99.41728331859264 -81.86677583771929, 70.6436647152336 -84.15292082959837)')
        result = prolong(float_line, front_prolong_len=1e-3, end_prolong_len=1e-3)
        self.assertEqual(2, len(result.coords))

    def test_prolong_negative_length(self):
        line = LineString([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)])
        result = prolong(line, front_prolong_len=-1.5)
        self.assertTrue(LineString([(1.5, 0), (2, 0), (2, 1), (2, 2)]).equals(result))

        result = prolong(line, front_prolong_len=-2.5)
        self.assertTrue(LineString([(2, 0.5), (2, 1), (2, 2)]).equals(result))

        result = prolong(line, end_prolong_len=-2.5)
        self.assertTrue(LineString([(0, 0), (1, 0), (1.5, 0)]).equals(result))

        result = prolong(line, front_prolong_len=2, end_prolong_len=-5)
        self.assertTrue(LineString([(-2, 0), (-1, 0)]).equals(result))

        result = prolong(line, front_prolong_len=-3, end_prolong_len=-2)
        self.assertTrue(LineString([(2, 1), (2, 0)]).equals(result))

        result = prolong(line, front_prolong_len=-4, end_prolong_len=-4)
        self.assertTrue(line.ext.reverse().equals(result))