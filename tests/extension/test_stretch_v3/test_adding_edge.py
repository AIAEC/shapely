import pytest

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.model.stretch.stretch_v3 import Stretch, EdgeSeq
from shapely.geometry import LineString, Polygon, Point, LinearRing


class TestAddingEdge:
    def test_add_empty_edge(self):
        stretch = Stretch()
        with pytest.raises(ValueError):
            stretch.add_edge(LineString())

    def test_add_edge_to_empty_stretch(self):
        stretch = Stretch()
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

        edge_seq = stretch.add_edge(LineString([(0, 0), (1, 1), (2, 3)]))
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 2
        assert edge_seq[0] == stretch.edge('(0,1)')
        assert edge_seq[1] == stretch.edge('(1,2)')
        assert len(stretch.pivots) == 3
        assert len(stretch.edges) == 2
        assert len(stretch.closures) == 0

    def test_add_duplicate_edge(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        edge_seq = stretch.add_edge(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]).exterior)

        assert len(edge_seq) == 4
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert edge_seq[0] == stretch.edge('(0,1)')
        assert edge_seq[1] == stretch.edge('(1,2)')
        assert edge_seq[2] == stretch.edge('(2,3)')
        assert edge_seq[3] == stretch.edge('(3,0)')

    def test_add_edge_with_duplicate_points(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

        result = stretch.add_edge(LineString([(0, 0), (0, 0), (1, 0), (1, 0)]))
        assert len(result) == 1
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 1
        assert len(stretch.closures) == 0

    def test_add_edge_with_points_almost_equal_to_pivots(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8

        edge_seq = stretch.add_edge(LineString([(1 + MATH_MIDDLE_EPS, 0 + MATH_MIDDLE_EPS),
                                                (2 - MATH_MIDDLE_EPS, 0 - MATH_MIDDLE_EPS),
                                                (2 + MATH_MIDDLE_EPS, 1 - MATH_MIDDLE_EPS)]),
                                    dist_tol_to_pivot=2 * MATH_MIDDLE_EPS)
        assert len(edge_seq) == 2
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert edge_seq[0] == stretch.edge('(1,4)')
        assert edge_seq[1] == stretch.edge('(4,5)')

    def test_add_edge_that_expanding_edge_and_expanded_by_pivot(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8

        edge_seq = stretch.add_edge(LineString([(1, 0.5), (1, 2)]))
        assert len(edge_seq) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 11
        assert edge_seq[0] == stretch.edge('(6,2)')
        assert edge_seq[1] == stretch.edge('(2,7)')
        assert edge_seq[0].reverse is stretch.edge('(2,6)')
        assert edge_seq[1].reverse is None

    def test_add_edge_that_is_the_substring_of_existed_edge(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8

        stretch.add_edge(LineString([(1, 0.4), (1, 0.6)]))
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12
        assert len(stretch.closure('0').exterior) == 6
        assert len(stretch.closure('1').exterior) == 6

    def test_add_edge_with_dist_tol_to_pivot_larger_than_length_of_line(self):
        stretch = Stretch()
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0

        edge_seq = stretch.add_edge(LineString([(0, 0),
                                                (MATH_MIDDLE_EPS / 10, 0),
                                                (MATH_MIDDLE_EPS / 10, MATH_MIDDLE_EPS / 10),
                                                (10, 0)]),
                                    dist_tol_to_pivot=MATH_MIDDLE_EPS,
                                    dist_tol_to_edge=MATH_MIDDLE_EPS)
        assert len(edge_seq) == 1
        assert len(stretch.pivots) == 2
        assert len(stretch.edges) == 1

        assert stretch.pivots[0].shape.equals(Point(0, 0))
        assert stretch.pivots[1].shape.equals(Point(10, 0))

    def test_add_edge_of_crack_alike_linear_ring(self):
        stretch = Stretch()
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0
        edge_seq = stretch.add_edge(LinearRing([(0, 0), (0.5, 0), (0.5, 0.5), (0.5, 0), (1, 0),
                                                (1, 1), (0, 1), (0, 0)]))
        assert len(edge_seq) == 7
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 7

    def test_default_cargo_after_adding_edge(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        stretch._default_edge_cargo_dict = {'test': 'edge'}
        edge_seq = stretch.add_edge(LineString([(0, 0), (1, 1)]))
        assert len(edge_seq) == 1
        assert edge_seq[0].cargo['test'] == 'edge'
