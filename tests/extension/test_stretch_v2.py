import pytest
from pytest import fixture

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.stretch_v2 import Pivot, DirectEdge, Stretch, ClosureSnapshot, DirectEdgeView
from shapely.geometry import Point, box, LineString


@fixture(scope='function')
def stretch_of_two_box() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_2_0 = Pivot(Point(2, 0), stretch)
    pivot_2_2 = Pivot(Point(2, 2), stretch)
    pivot_0_2 = Pivot(Point(0, 2), stretch)
    pivot_3_0 = Pivot(Point(3, 0), stretch)
    pivot_3_1 = Pivot(Point(3, 1), stretch)
    pivot_2_1 = Pivot(Point(2, 1), stretch)
    edges = [DirectEdge(pivot_0_0, pivot_2_0, stretch),
             DirectEdge(pivot_2_0, pivot_2_1, stretch),
             DirectEdge(pivot_2_1, pivot_2_2, stretch),
             DirectEdge(pivot_2_2, pivot_0_2, stretch),
             DirectEdge(pivot_0_2, pivot_0_0, stretch),
             DirectEdge(pivot_2_0, pivot_3_0, stretch),
             DirectEdge(pivot_3_0, pivot_3_1, stretch),
             DirectEdge(pivot_3_1, pivot_2_1, stretch),
             DirectEdge(pivot_2_1, pivot_2_0, stretch)]
    stretch.pivots = [pivot_0_0, pivot_2_0, pivot_2_2, pivot_0_2, pivot_3_0, pivot_3_1, pivot_2_1]
    stretch.edges = edges
    return stretch


class TestPivot:
    def test_equality(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        assert stretch.pivots[0] == stretch.pivots[0]
        assert stretch.pivots[0] != stretch.pivots[1]

    def test_repr(self, stretch_of_two_box):
        pivot = stretch_of_two_box.pivots[0]
        assert len(str(pivot)) > 0


class TestDirectEdge:
    def test_direct_edge_view_has_same_hash_with_direct_edge(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = DirectEdge(stretch.query_pivots(Point(2, 2))[0],
                          stretch.query_pivots(Point(0, 2))[0],
                          stretch)

        edge_view = DirectEdgeView(stretch.query_pivots(Point(2, 2))[0],
                                   stretch.query_pivots(Point(0, 2))[0],
                                   stretch)
        assert edge == edge_view
        assert hash(edge) == hash(edge_view)
        assert edge in stretch.edges
        assert edge_view in stretch.edges
        assert edge in {edge_view}

    def test_expand(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (2, 0)]))

        origin_num_pivots = len(stretch.pivots)
        origin_num_edges = len(stretch.edges)

        # add to endpoints' pivot
        new_pivot = edge.expand(Point(MATH_EPS / 10, 0))
        assert new_pivot == stretch.pivots[0]
        assert origin_num_pivots == len(stretch.pivots)
        assert origin_num_edges == len(stretch.edges)

        edge = stretch.query_edges(Point(2, 0.5))[0]
        assert edge.shape.equals(LineString([(2, 0), (2, 1)]))
        new_pivot = edge.expand(Point(2, 0.5))
        assert new_pivot != stretch.pivots[0]
        assert new_pivot != stretch.pivots[1]
        assert new_pivot.shape.equals(Point(2, 0.5))
        assert len(new_pivot.out_edges) == 2
        assert len(new_pivot.in_edges) == 2
        assert origin_num_pivots + 1 == len(stretch.pivots)
        assert origin_num_edges + 2 == len(stretch.edges)

        pivot = stretch.query_pivots(Point(2, 1))[0]
        assert len(pivot.out_edges) == 2
        assert len(pivot.in_edges) == 2


class TestStretch:
    def test_query_pivot(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        result = stretch.query_pivots(Point(0, 0))
        assert len(result) == 1
        assert result[0] == stretch.pivots[0]

    def test_query_edges(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        result = stretch.query_edges(Point(1, 0), buffer=MATH_EPS)
        assert len(result) == 1

        result = stretch.query_edges(box(2, 0, 2.1, 0.1))
        assert len(result) == 4

    def test_add_pivot(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        pivot0 = stretch.pivots[0]
        result = stretch.add_pivot(Point(MATH_EPS / 10, 0), reuse_existing=True, dist_tol=MATH_EPS)
        assert pivot0 == result

        result = stretch.add_pivot(Point(-MATH_EPS / 10, 0), reuse_existing=True, dist_tol=0)
        assert pivot0 != result

        result = stretch.add_pivot(Point(0, 0), reuse_existing=False, dist_tol=MATH_EPS)
        assert pivot0 != result

        with pytest.raises(ValueError):
            stretch.add_pivot(Point())

        with pytest.raises(ValueError):
            stretch.add_pivot(1)

    def test_add_closure(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        origin_num_pivots: int = len(stretch.pivots)

        result = stretch.add_closure(box(0, 0, 2, 2), reuse_existing=True, dist_tol=MATH_EPS)
        assert len(result) == 4
        assert origin_num_pivots == len(stretch.pivots)

        result = stretch.add_closure(box(2, 1, 3, 2), reuse_existing=True, dist_tol=MATH_EPS)
        assert len(result) == 4
        assert origin_num_pivots + 1 == len(stretch.pivots)

    def test_remove_closure(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        closures = sorted(stretch.closure_snapshot().closures,
                          key=lambda closure: closure.shape.area)
        stretch.remove_closure(closures[0])

        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5

        stretch.remove_closure(closures[1])

        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0

    def test_union_closure(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        closures = stretch.closure_snapshot().closures
        assert len(closures) == 2

        origin_num_pivots = len(stretch.pivots)
        stretch.union_closures(closures)
        assert origin_num_pivots == len(stretch.pivots)
        closures = stretch.closure_snapshot().closures
        assert 1 == len(closures)

    def test_split_by_failing_splitter(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        origin_num_pivots = len(stretch.pivots)
        origin_num_edges = len(stretch.edges)

        # split by a failing splitter
        assert not stretch.split_by(LineString([(0.9, 0.9), (1.1, 1.1)]))

        assert len(stretch.pivots) == origin_num_pivots
        assert len(stretch.edges) == origin_num_edges
        assert len(stretch.closure_snapshot().closures) == 2

    def test_split_by_simple_splitter(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        assert stretch.split_by(LineString([(1, 0), (1, 2)]))

        closures = stretch.closure_snapshot().closures
        assert len(closures) == 3
        closures.sort(key=lambda closure: closure.shape.centroid.x)
        assert closures[0].shape.equals(box(0, 0, 1, 2))
        assert closures[1].shape.equals(box(1, 0, 2, 2))
        assert closures[2].shape.equals(box(2, 0, 3, 1))

    def test_split_by_splitter_across_several_closures(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        origin_num_pivots = len(stretch.pivots)

        assert stretch.split_by(LineString([(0, 0.5), (3, 0.5)]))
        closures = stretch.closure_snapshot().closures
        assert len(closures) == 4
        assert len(stretch.pivots) == origin_num_pivots + 3
        assert len(stretch.edges) == 17

    def test_split_by_splitter_touching_edges(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        origin_num_pivots = len(stretch.pivots)
        origin_num_edges = len(stretch.edges)

        assert stretch.split_by(LineString([(0, 1), (3, 1)]))
        closures = stretch.closure_snapshot().closures
        assert len(closures) == 3
        assert len(stretch.pivots) == origin_num_pivots + 1
        assert len(stretch.edges) == origin_num_edges + 3


class TestClosureSnapshot:
    def test_next_edge(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = DirectEdge(stretch.query_pivots(Point(2, 2))[0],
                          stretch.query_pivots(Point(0, 2))[0],
                          stretch)
        result = ClosureSnapshot.next_edge(edge)
        assert result.shape.equals(LineString([(0, 2), (0, 0)]))

        result = ClosureSnapshot.next_edge(result)
        assert result.shape.equals(LineString([(0, 0), (2, 0)]))

        result = ClosureSnapshot.next_edge(result)
        assert result.shape.equals(LineString([(2, 0), (2, 1)]))

        result = ClosureSnapshot.next_edge(result)
        assert result.shape.equals(LineString([(2, 1), (2, 2)]))

        result = ClosureSnapshot.next_edge(result)
        assert result.shape.equals(LineString([(2, 2), (0, 2)]))

        edge = DirectEdge(stretch.query_pivots(Point(2, 0))[0],
                          stretch.query_pivots(Point(3, 0))[0],
                          stretch)

        result = ClosureSnapshot.next_edge(edge)
        assert result.shape.equals(LineString([(3, 0), (3, 1)]))

        result = ClosureSnapshot.next_edge(result)
        assert result.shape.equals(LineString([(3, 1), (2, 1)]))

        result = ClosureSnapshot.next_edge(result)
        assert result.shape.equals(LineString([(2, 1), (2, 0)]))

    def test_create_closure_snapshot_from_stretch(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        closure_snapshot = ClosureSnapshot.create_from(stretch)
        assert len(closure_snapshot.closures) == 2
        closures = sorted(closure_snapshot.closures, key=lambda closure: closure.shape.area)
        assert closures[0].shape.equals(box(2, 0, 3, 1))
        assert closures[1].shape.equals(box(0, 0, 2, 2))
