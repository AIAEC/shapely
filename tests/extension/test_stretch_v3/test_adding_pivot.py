from collections import OrderedDict

import pytest

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.model.interval import Interval
from shapely.extension.model.stretch.stretch_v3 import Stretch, Edge
from shapely.geometry import Point, LineString


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


class TestSubEdge:
    def test_sub_edge_absolute_mode(self, stretch_box):
        stretch = stretch_box

        edge = stretch.edges[0]
        assert len(stretch.edges) == 4
        assert len(stretch.pivots) == 4
        assert len(stretch.closures) == 1

        result = edge.sub_edge((0.5, 0.75), absolute=True)
        assert isinstance(result, Edge)
        assert result.shape.equals(LineString([(0.5, 0), (0.75, 0)]))
        assert len(stretch.edges) == 6
        assert len(stretch.pivots) == 6
        assert len(stretch.closures) == 1

    def test_sub_edge_relative_mode(self, stretch_box):
        stretch = stretch_box

        edge = stretch.edges[0]
        assert len(stretch.edges) == 4
        assert len(stretch.pivots) == 4
        assert len(stretch.closures) == 1

        result = edge.sub_edge((0.1, 0.9), absolute=False)
        assert isinstance(result, Edge)
        assert result.shape.equals(LineString([(0.1, 0), (0.9, 0)]))
        assert len(stretch.edges) == 6
        assert len(stretch.pivots) == 6
        assert len(stretch.closures) == 1

    def test_sub_edge_with_reverse_closure(self, stretch_2_boxes):
        stretch = stretch_2_boxes

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges
        assert len(stretch.edges) == 8
        assert len(stretch.pivots) == 6
        assert len(stretch.closures) == 2

        result = edge.sub_edge((0.3, 0.6), absolute=True)
        assert isinstance(result, Edge)
        assert result.closure is stretch.closure('0')
        assert result.shape.equals(LineString([(1, 0.3), (1, 0.6)]))
        assert result.reverse is not None
        assert result.reverse_closure is stretch.closure('1')
        assert result in stretch.edges
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12
        assert len(stretch.closures) == 2

    def test_sub_edge_with_wrong_interval(self, stretch_box):
        stretch = stretch_box

        edge = stretch.edges[0]

        with pytest.raises(AssertionError):
            edge.sub_edge((0.2, 0.1), absolute=True)

        with pytest.raises(AssertionError):
            edge.sub_edge((0.5, 0.5), absolute=True)

    def test_sub_edge_attaching_to_existed_pivot(self, stretch_box):
        stretch = stretch_box

        edge = stretch.edges[0]
        assert len(stretch.edges) == 4
        assert len(stretch.pivots) == 4
        assert len(stretch.closures) == 1

        result = edge.sub_edge(Interval(0.5, 1 - MATH_MIDDLE_EPS), absolute=True, dist_tol_to_pivot=2 * MATH_MIDDLE_EPS)
        assert isinstance(result, Edge)
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert len(stretch.closures) == 1
        assert result.shape.equals(LineString([(0.5, 0), (1, 0)]))

    def test_default_pivot_cargo_when_add_pivot(self):
        stretch = Stretch(default_pivot_cargo_dict={'test': 'pivot'})
        pivot = stretch.add_pivot(Point(0, 0))
        assert pivot.cargo['test'] == 'pivot'
