from collections import OrderedDict

import pytest

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.model.stretch.stretch_v3 import Stretch, Edge
from shapely.geometry import Point


class TestAddingPivot:
    def test_add_empty_point(self):
        stretch = Stretch()
        with pytest.raises(ValueError):
            stretch.add_pivot(Point())

    def test_add_point(self):
        stretch = Stretch()
        assert len(stretch.pivots) == 0
        stretch.add_pivot(Point(0, 0))
        assert len(stretch.pivots) == 1

    def test_add_duplicate_point(self):
        stretch = Stretch()
        stretch.add_pivot(Point(0, 0))
        assert len(stretch.pivots) == 1

        stretch.add_pivot(Point(0, 0))
        assert len(stretch.pivots) == 1

    def test_add_point_almost_equal_to_pivot(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        assert len(stretch.pivots) == 4

        pivot = stretch.add_pivot(Point(MATH_MIDDLE_EPS, MATH_MIDDLE_EPS), dist_tol_to_pivot=2 * MATH_MIDDLE_EPS)
        assert len(stretch.pivots) == 4
        assert pivot is stretch.pivot('0')

    def test_add_pivot_that_attaching_to_existed_edge(self, stretch_box):
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 4

        stretch_box.add_pivot(Point(0.5, 0))
        assert len(stretch_box.pivots) == 5
        assert len(stretch_box.edges) == 5

    def test_add_pivot_that_attaching_to_existed_edges(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        crossing_edge0 = Edge('0', '2', stretch)
        crossing_edge1 = Edge('1', '3', stretch)
        stretch._edge_map = OrderedDict([(e.id, e) for e in (crossing_edge0, crossing_edge1)])

        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 2

        pivot = stretch.add_pivot(Point(0.5, 0.5))
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 4
        assert pivot in stretch.pivots
        assert len(pivot.in_edges) == 2
        assert len(pivot.out_edges) == 2

        assert crossing_edge0 not in pivot.in_edges
        assert crossing_edge1 not in pivot.in_edges
        assert crossing_edge0 not in stretch.edges
        assert crossing_edge1 not in stretch.edges
        assert all(edge in stretch.edges for edge in pivot.in_edges)

    def test_add_pivot_almost_attach_to_existed_edges(self, stretch_4_dangling_edge):
        stretch = stretch_4_dangling_edge
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4

        pivot = stretch.add_pivot(Point(0.5, MATH_MIDDLE_EPS), dist_tol_to_edge=2 * MATH_MIDDLE_EPS)
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert pivot in stretch.pivots
