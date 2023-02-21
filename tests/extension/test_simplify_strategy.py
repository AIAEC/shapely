from typing import List
from unittest import TestCase

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.strategy.simplify_strategy import ConservativeSimplifyStrategy, RingSimplifyStrategy, \
    NativeSimplifyStrategy, BufferSimplifyStrategy
from shapely.geometry import box, LinearRing, Point, Polygon, LineString, MultiPolygon
from shapely.wkt import loads


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


def test_simplify_linear_ring():
    start_in_middle_ring = LinearRing([(5, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
    assert start_in_middle_ring.coords[0] == start_in_middle_ring.coords[-1]
    assert len(start_in_middle_ring.coords) == 6
    assert 6 == len(start_in_middle_ring.ext.decompose(Point).to_list())

    native_simplified = start_in_middle_ring.simplify(1)
    assert 6 == len(native_simplified.ext.decompose(Point).to_list())

    ring_simplified = start_in_middle_ring.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=1))[0]
    assert 5 == len(ring_simplified.ext.decompose(Point).to_list())
    assert 5 == len(ring_simplified.coords)
    assert isinstance(ring_simplified, LinearRing)


def test_ring_simplify_strategy():
    start_in_middle_ring = LinearRing([(50, 0), (100, 0), (100, 100), (0, 100), (0, 0)])
    simplified = start_in_middle_ring.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=0))[0]
    assert 5 == len(simplified.ext.decompose(Point).to_list())
    assert isinstance(simplified, type(start_in_middle_ring))
    assert LinearRing([(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]) == simplified

    small_ring = box(80, 80, 90, 90).exterior
    simplified = small_ring.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=0))[0]
    assert 5 == len(simplified.ext.decompose(Point).to_list())
    assert isinstance(simplified, type(small_ring))

    poly: Polygon = box(10, 10, 20, 20)
    simplified = poly.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=1))[0]
    assert 5 == len(simplified.ext.decompose(Point).to_list())
    assert isinstance(simplified, type(poly))

    p = Point(0, 0)
    simplified = p.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=1))[0]
    assert 1 == len(simplified.ext.decompose(Point).to_list())
    assert isinstance(simplified, type(p))

    line = LineString([(0, 0), (1, 0)])
    simplified = line.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=1))[0]
    assert 2 == len(simplified.ext.decompose(Point).to_list())
    assert isinstance(simplified, type(line))

    ring_line = LineString([(50, 0), (100, 0), (100, 100), (0, 100), (0, 0), (50, 0)])
    simplified = ring_line.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=0))[0]
    assert 6 == len(simplified.ext.decompose(Point).to_list())
    assert ring_line == simplified
    assert isinstance(simplified, type(ring_line))

    poly = Polygon(shell=start_in_middle_ring.coords,
                   holes=[small_ring, LinearRing([(50, 50), (60, 50), (60, 60), (40, 60), (40, 50)])])
    simplified = poly.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=0))[0]
    assert 5 * 3 == len(simplified.ext.decompose(Point).to_list())
    pol = Polygon(shell=[(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)],
                  holes=[small_ring, [(40, 50), (60, 50), (60, 60), (40, 60)]])
    assert pol == simplified
    assert isinstance(simplified, type(poly))

    multi_poly = MultiPolygon([poly, poly])
    simplified = multi_poly.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=0))

    assert [pol, pol] == simplified
    assert isinstance(simplified, List)


def test_simplify_invalid_ring_no_raise():
    self_intersection_ring: LinearRing = loads(
        "LINEARRING (4.75 0.5, 4.75 0, 2 2.75, 198.860912703474 2.75, 293.360912703474 97.25, 197.25 97.25, 197.25 197.25, 102.75 197.25, 102.75 98.86091270347399, 4.75 0.8609127034739856, 4.75 0.5)")
    assert not self_intersection_ring.is_valid
    # assert no raise
    ring = self_intersection_ring.ext.simplify(strategy=RingSimplifyStrategy(simplify_dist=0.1))[0]
    assert isinstance(ring, LinearRing)
    assert len(ring.coords) == 10

    ring = self_intersection_ring.ext.simplify(strategy=NativeSimplifyStrategy(simplify_dist=0.1))[0]
    assert isinstance(ring, LinearRing)
    assert len(ring.coords) == 11

    ring = self_intersection_ring.ext.simplify(strategy=BufferSimplifyStrategy().round(buffer_dist=0.1))[0]
    assert isinstance(ring, LinearRing)
    assert len(ring.coords) == 11

    ring = self_intersection_ring.ext.simplify(strategy=ConservativeSimplifyStrategy(area_diff_tolerance=0.1))[0]
    assert isinstance(ring, LinearRing)
    assert len(ring.coords) == 11
