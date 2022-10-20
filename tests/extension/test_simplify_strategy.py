from unittest import TestCase

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.strategy.simplify_strategy import ConservativeSimplifyStrategy
from shapely.geometry import box


class SimplifyStrategyTest(TestCase):
    def test_conservative_strategy(self):
        poly = box(0, 0, 1, 1)
        burr_len = 0.1
        burr_height = MATH_MIDDLE_EPS
        burr = box(0.5, 1 - burr_height, 0.5 + burr_len, 1 + burr_height)
        poly_with_burr = poly.ext.union(burr)

        simplified_geom = ConservativeSimplifyStrategy._conservative_simplify(geom=poly_with_burr,
                                                                              simplify_dist=2 * burr_height,
                                                                              area_diff_tolerance=2 * burr_len * burr_height)
        self.assertNotEqual(simplified_geom.area, poly_with_burr.area)
        self.assertEqual(simplified_geom.area, poly_with_burr.simplify(2 * burr_height).area)
        self.assertEqual(1, simplified_geom.area)

        simplified_geom = ConservativeSimplifyStrategy._conservative_simplify(geom=poly_with_burr,
                                                                              simplify_dist=2 * burr_height,
                                                                              area_diff_tolerance=0.5 * burr_len * burr_height)
        self.assertEqual(simplified_geom.area, poly_with_burr.area)
        self.assertNotEqual(simplified_geom.area, poly_with_burr.simplify(2 * burr_height).area)
        self.assertNotEqual(1, simplified_geom.area)

        simplified_geom = ConservativeSimplifyStrategy._conservative_simplify(geom=poly_with_burr,
                                                                              simplify_dist=0.5 * burr_height,
                                                                              area_diff_tolerance=2 * burr_len * burr_height)
        self.assertEqual(simplified_geom.area, poly_with_burr.area)
        self.assertNotEqual(simplified_geom.area, poly_with_burr.simplify(2 * burr_height).area)
        self.assertNotEqual(1, simplified_geom.area)
