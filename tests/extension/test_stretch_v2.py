import pytest
from pytest import fixture

from shapely.extension.constant import MATH_EPS
from shapely.extension.model import Vector
from shapely.extension.model.stretch_v2 import Pivot, DirectEdge, Stretch, ClosureSnapshot, DirectEdgeView, \
    OffsetStrategy, ClosureView, StretchFactory
from shapely.geometry import Point, box, LineString
from shapely.wkt import loads


@fixture
def stretch_of_single_box() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_2_0 = Pivot(Point(2, 0), stretch)
    pivot_2_2 = Pivot(Point(2, 2), stretch)
    pivot_0_2 = Pivot(Point(0, 2), stretch)
    edges = [DirectEdge(pivot_0_0, pivot_2_0, stretch),
             DirectEdge(pivot_2_0, pivot_2_2, stretch),
             DirectEdge(pivot_2_2, pivot_0_2, stretch),
             DirectEdge(pivot_0_2, pivot_0_0, stretch)]
    stretch.pivots = [pivot_0_0, pivot_2_0, pivot_2_2, pivot_0_2]
    stretch.edges = edges
    return stretch


@fixture
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


@fixture
def stretch_of_two_box_with_collinear_edge() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_2_0 = Pivot(Point(2, 0), stretch)
    pivot_2_2 = Pivot(Point(2, 2), stretch)
    pivot_0_2 = Pivot(Point(0, 2), stretch)
    pivot_3_0 = Pivot(Point(3, 0), stretch)
    pivot_3_2 = Pivot(Point(3, 2), stretch)
    pivot_2_1 = Pivot(Point(2, 1), stretch)
    edges = [DirectEdge(pivot_0_0, pivot_2_0, stretch),
             DirectEdge(pivot_2_0, pivot_2_1, stretch),
             DirectEdge(pivot_2_1, pivot_2_2, stretch),
             DirectEdge(pivot_2_2, pivot_0_2, stretch),
             DirectEdge(pivot_0_2, pivot_0_0, stretch),
             DirectEdge(pivot_2_0, pivot_3_0, stretch),
             DirectEdge(pivot_3_0, pivot_3_2, stretch),
             DirectEdge(pivot_3_2, pivot_2_2, stretch),
             DirectEdge(pivot_2_2, pivot_2_1, stretch),
             DirectEdge(pivot_2_1, pivot_2_0, stretch)]
    stretch.pivots = [pivot_0_0, pivot_2_0, pivot_2_2, pivot_0_2, pivot_3_0, pivot_3_2, pivot_2_1]
    stretch.edges = edges
    return stretch


@fixture
def stretch_of_single_box_with_glitch() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_1_0 = Pivot(Point(1, 0), stretch)
    pivot_2_0 = Pivot(Point(2, 0), stretch)
    pivot_1_1 = Pivot(Point(1, 1), stretch)
    pivot_0_1 = Pivot(Point(0, 1), stretch)
    edges = [DirectEdge(pivot_0_0, pivot_1_0, stretch),
             DirectEdge(pivot_1_0, pivot_2_0, stretch),
             DirectEdge(pivot_2_0, pivot_1_0, stretch),
             DirectEdge(pivot_1_0, pivot_1_1, stretch),
             DirectEdge(pivot_1_1, pivot_0_1, stretch),
             DirectEdge(pivot_0_1, pivot_0_0, stretch)]
    stretch.pivots = [pivot_0_0, pivot_1_0, pivot_2_0, pivot_1_1, pivot_0_1]
    stretch.edges = edges
    return stretch


@fixture
def stretch_of_single_concave_box() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_2_0 = Pivot(Point(2, 0), stretch)
    pivot_2_2 = Pivot(Point(2, 2), stretch)
    pivot_1_1 = Pivot(Point(1, 1), stretch)
    pivot_0_2 = Pivot(Point(0, 2), stretch)
    edges = [DirectEdge(pivot_0_0, pivot_2_0, stretch),
             DirectEdge(pivot_2_0, pivot_2_2, stretch),
             DirectEdge(pivot_2_2, pivot_1_1, stretch),
             DirectEdge(pivot_1_1, pivot_0_2, stretch),
             DirectEdge(pivot_0_2, pivot_0_0, stretch)]
    stretch.pivots = [pivot_0_0, pivot_2_0, pivot_2_2, pivot_1_1, pivot_0_2]
    stretch.edges = edges
    return stretch


@fixture
def stretch_of_single_box_collinear_edge() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_2_0 = Pivot(Point(2, 0), stretch)
    pivot_2_2 = Pivot(Point(2, 2), stretch)
    pivot_1_2 = Pivot(Point(1, 2), stretch)
    pivot_0_2 = Pivot(Point(0, 2), stretch)
    edges = [DirectEdge(pivot_0_0, pivot_2_0, stretch),
             DirectEdge(pivot_2_0, pivot_2_2, stretch),
             DirectEdge(pivot_2_2, pivot_1_2, stretch),
             DirectEdge(pivot_1_2, pivot_0_2, stretch),
             DirectEdge(pivot_0_2, pivot_0_0, stretch)]
    stretch.pivots = [pivot_0_0, pivot_2_0, pivot_2_2, pivot_1_2, pivot_0_2]
    stretch.edges = edges
    return stretch


@fixture
def stretch_of_box_and_triangle() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_1_0 = Pivot(Point(1, 0), stretch)
    pivot_1_1 = Pivot(Point(1, 1), stretch)
    pivot_0_1 = Pivot(Point(0, 1), stretch)
    pivot_2_1 = Pivot(Point(2, 1), stretch)

    edges = [DirectEdge(pivot_0_0, pivot_1_0, stretch),
             DirectEdge(pivot_1_0, pivot_1_1, stretch),
             DirectEdge(pivot_1_1, pivot_0_1, stretch),
             DirectEdge(pivot_0_1, pivot_0_0, stretch),
             DirectEdge(pivot_1_0, pivot_2_1, stretch),
             DirectEdge(pivot_2_1, pivot_1_1, stretch),
             DirectEdge(pivot_1_1, pivot_1_0, stretch)]

    stretch.pivots = [pivot_0_0, pivot_1_0, pivot_1_1, pivot_0_1, pivot_2_1]
    stretch.edges = edges
    return stretch


@fixture
def stretch_for_offset() -> Stretch:
    stretch = Stretch([], [])
    pivot_0_0 = Pivot(Point(0, 0), stretch)
    pivot_1_0 = Pivot(Point(1, 0), stretch)
    pivot_1_1 = Pivot(Point(1, 1), stretch)
    pivot_1_n1 = Pivot(Point(1, -1), stretch)
    pivot_10_n1 = Pivot(Point(10, -1), stretch)
    pivot_10_n10 = Pivot(Point(10, -10), stretch)
    pivot_0_n10 = Pivot(Point(0, -10), stretch)

    edges = [
        DirectEdge(pivot_0_0, pivot_1_0, stretch),
        DirectEdge(pivot_1_0, pivot_1_1, stretch),
        DirectEdge(pivot_1_1, pivot_0_0, stretch),
        DirectEdge(pivot_1_0, pivot_0_0, stretch),
        DirectEdge(pivot_0_0, pivot_0_n10, stretch),
        DirectEdge(pivot_0_n10, pivot_10_n10, stretch),
        DirectEdge(pivot_10_n10, pivot_10_n1, stretch),
        DirectEdge(pivot_10_n1, pivot_1_n1, stretch),
        DirectEdge(pivot_1_n1, pivot_1_0, stretch)
    ]

    stretch.pivots = [pivot_0_0, pivot_1_0, pivot_1_1, pivot_1_n1, pivot_10_n1, pivot_10_n10, pivot_0_n10]
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

    def test_next(self, stretch_of_box_and_triangle):
        stretch = stretch_of_box_and_triangle
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (1, 0)]))
        assert edge.next.shape.equals(LineString([(1, 0), (1, 1)]))

        edge = stretch.edges[-1]
        assert edge.shape.equals(LineString([(1, 1), (1, 0)]))
        assert edge.next.shape.equals(LineString([(1, 0), (2, 1)]))

    def test_next_for_2_box(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = DirectEdge(stretch.query_pivots(Point(2, 2))[0],
                          stretch.query_pivots(Point(0, 2))[0],
                          stretch)
        result = edge.next
        assert result.shape.equals(LineString([(0, 2), (0, 0)]))

        result = result.next
        assert result.shape.equals(LineString([(0, 0), (2, 0)]))

        result = result.next
        assert result.shape.equals(LineString([(2, 0), (2, 1)]))

        result = result.next
        assert result.shape.equals(LineString([(2, 1), (2, 2)]))

        result = result.next
        assert result.shape.equals(LineString([(2, 2), (0, 2)]))

        edge = DirectEdge(stretch.query_pivots(Point(2, 0))[0],
                          stretch.query_pivots(Point(3, 0))[0],
                          stretch)

        result = edge.next
        assert result.shape.equals(LineString([(3, 0), (3, 1)]))

        result = result.next
        assert result.shape.equals(LineString([(3, 1), (2, 1)]))

        result = result.next
        assert result.shape.equals(LineString([(2, 1), (2, 0)]))

    def test_previous(self, stretch_of_box_and_triangle):
        stretch = stretch_of_box_and_triangle
        edge = stretch.edges[-1]
        assert edge.shape.equals(LineString([(1, 1), (1, 0)]))
        assert edge.previous.shape.equals(LineString([(2, 1), (1, 1)]))

        edge = stretch.edges[-3]
        assert edge.shape.equals(LineString([(1, 0), (2, 1)]))
        assert edge.previous.shape.equals(LineString([(1, 1), (1, 0)]))


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

    def test_add_closure_case0(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        origin_num_pivots: int = len(stretch.pivots)

        result = stretch.add_closure(box(0, 0, 2, 2), dist_tol=MATH_EPS)
        assert result
        assert origin_num_pivots == len(stretch.pivots)

        result = stretch.add_closure(box(2, 1, 3, 2), dist_tol=MATH_EPS)
        assert result
        assert origin_num_pivots + 1 == len(stretch.pivots)

    def test_add_closure_case1(self, stretch_of_single_box):
        stretch = stretch_of_single_box
        origin_num_pivots: int = len(stretch.pivots)
        origin_num_edges: int = len(stretch.edges)

        stretch.add_closure(box(2, 0, 3, 4), dist_tol=MATH_EPS)
        assert len(stretch.pivots) == origin_num_pivots + 3
        assert len(stretch.edges) == origin_num_edges + 5

    def test_add_closure_case2(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 9
        stretch.add_closure(box(0, 0, 1, 1), dist_tol=MATH_EPS)
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 15
        closures = stretch.closure_snapshot().closures
        assert len(closures) == 3

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

    def test_split_by_spliter_crosing_pivot(self, stretch_of_single_concave_box):
        stretch = stretch_of_single_concave_box
        assert stretch.split_by(LineString([(0, 1 - MATH_EPS / 10), (2, 1 - MATH_EPS / 10)]))
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 11
        closures = stretch.closure_snapshot().closures
        assert len(closures) == 3

    def test_remove_dangling_edges(self, stretch_of_single_box_with_glitch):
        stretch = stretch_of_single_box_with_glitch
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 6
        stretch.remove_dangling_edges()
        assert len(stretch.edges) == 4

    def test_simplify_edges_0(self, stretch_of_single_box_collinear_edge):
        stretch = stretch_of_single_box_collinear_edge
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        stretch.simplify_edges()
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4

    def test_simplify_edges_1(self, stretch_of_two_box_with_collinear_edge):
        stretch = stretch_of_two_box_with_collinear_edge
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 10
        stretch.simplify_edges()
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8


class TestStretchFactory:
    def test_create(self):
        multi_poly = loads(
            'MULTIPOLYGON (((-53.05822597367154 -95.01209220619683, -61.887666776967436 -86.77312703550751, -61.88766677696752 -73.71209220612593, -64.93766677696746 -73.71209220612593, -64.93766677696748 -45.56209221839969, -27.087666826184126 -45.56209221839969, -27.087666826184126 -95.01209220619683, -53.05822597367154 -95.01209220619683)), ((-64.93766677696749 -20.412093737098296, -27.087666826184126 -20.412093737098296, -27.087666826184126 -45.56209219839969, -64.93766677696748 -45.56209219839969, -64.93766677696749 -20.412093737098296)), ((-27.087666806184124 44.03790778418159, -10.787666816042908 44.03790778418159, 22.712333172566055 44.03790778418159, 22.712333172566055 33.837907793117665, 22.712333172566055 -4.012092247400119, 22.712333172566055 -93.60833474224941, 3.0011820026950033 -95.01209220619683, -27.087666806184124 -95.01209220619683, -27.087666806184124 -45.56209220839969, -27.087666806184124 -20.412093727098295, -27.087666806184124 16.237896621901427, -27.087666806184124 44.03790778418159)), ((-64.9376667769675 16.237896611901427, -27.087666826184126 16.237896611901427, -27.087666826184126 -20.412093717098294, -64.93766677696749 -20.412093717098294, -64.9376667769675 16.237896611901427)), ((-64.93766677696752 44.0379077938029, -27.087666826184126 44.03790778418159, -27.087666826184126 16.237896631901428, -64.9376667769675 16.237896631901428, -64.93766677696752 44.0379077938029)), ((-62.83766677696752 44.03790780418159, -62.83766677696752 85.73790777799447, -27.087666826184126 85.73790777799447, -27.087666826184126 44.03790780418159, -62.83766677696752 44.03790780418159)), ((-27.087666806184124 44.03790780418159, -27.087666806184124 85.73790777799447, -10.787666826042908 85.73790777799447, -10.787666826042908 44.03790780418159, -27.087666806184124 44.03790780418159)), ((14.18462981050255 85.73790779799445, -10.787666816042908 85.73790779799445, -27.087666816184125 85.73790779799445, -62.83766677696752 85.73790779799445, -62.83766677696752 92.37471221102714, -39.45873254462499 124.73790779380306, -17.783212025386398 124.73790779380306, 14.18462981050255 85.73790779799445)), ((56.66367611144763 -83.41471062464564, 54.012333192565926 -84.24945464645742, 54.012333192565926 -50.96209225740062, 88.83678942334107 -50.96209225740062, 74.17985788639731 -71.02158696273534, 56.66367611144763 -83.41471062464564)), ((54.012333172565924 -50.96209224740062, 54.012333172565924 -84.2494546527542, 24.746451140575914 -93.4634721588551, 22.712333192566057 -93.60833474082509, 22.712333192566057 -4.012092257400119, 54.012333172565924 -4.012092257400119, 54.012333172565924 -13.112092206882949, 54.012333172565924 -50.96209224740062)), ((100.26061454987092 -35.32743100086873, 88.83678943795454 -50.96209223740062, 54.012333192565926 -50.96209223740062, 54.012333192565926 -13.11209221688295, 95.21081356160086 -13.11209221688295, 100.01517397290434 -18.973296641710476, 100.26061454987092 -35.32743100086873)), ((54.012333192565926 -13.112092196882948, 54.012333192565926 -4.012092257400119, 87.7516504989699 -4.012092257400119, 95.21081354520709 -13.112092196882948, 54.012333192565926 -13.112092196882948)), ((54.012333182565925 -4.012092237400119, 22.712333192566057 -4.012092237400119, 22.712333192566057 33.837907783117664, 56.72645011656729 33.837907783117664, 87.75165048257614 -4.012092237400119, 54.012333182565925 -4.012092237400119)), ((22.712333192566057 33.837907803117666, 22.712333192566057 44.03790778418159, 48.36562994233339 44.03790778418159, 56.72645010017352 33.837907803117666, 22.712333192566057 33.837907803117666)), ((22.712333182566056 44.03790780418159, -10.787666806042907 44.03790780418159, -10.787666806042907 85.73790777799447, 14.18462982689631 85.73790777799447, 48.36562992593962 44.03790780418159, 22.712333182566056 44.03790780418159)))')
        stretch = StretchFactory(1e-6).create(multi_poly)
        closures = stretch.closure_snapshot().closures
        assert len(closures) == 15


class TestClosureSnapshot:
    def test_create_closure_snapshot_from_stretch(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        closure_snapshot = ClosureSnapshot.create_from(stretch)
        assert len(closure_snapshot.closures) == 2
        closures = sorted(closure_snapshot.closures, key=lambda closure: closure.shape.area)
        assert closures[0].shape.equals(box(2, 0, 3, 1))
        assert closures[1].shape.equals(box(0, 0, 2, 2))


class TestOffsetStrategy:
    def test_shrinking_closure(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = stretch.query_edges(Point(2, 0.5))[0]
        assert edge.shape.equals(LineString([(2, 0), (2, 1)]))

        closure = OffsetStrategy(edge, Vector(-1, 0)).shrinking_closure
        assert isinstance(closure, ClosureView)
        assert closure.shape.equals(box(0, 0, 2, 2))

        closure = OffsetStrategy(edge, Vector(1, 0)).shrinking_closure
        assert isinstance(closure, ClosureView)
        assert closure.shape.equals(box(2, 0, 3, 1))

        edge = stretch.query_edges(Point(2.5, 1))[0]
        assert edge.shape.equals(LineString([(3, 1), (2, 1)]))

        closure = OffsetStrategy(edge, Vector(0, 1)).shrinking_closure
        assert closure is None

        closure = OffsetStrategy(edge, Vector(0, -1)).shrinking_closure
        assert isinstance(closure, ClosureView)
        assert closure.shape.equals(box(2, 0, 3, 1))

    def test_does_from_pivot_use_perpendicular_mode_case0(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (2, 0)]))
        assert not OffsetStrategy.does_from_pivot_use_perpendicular_mode(edge, Vector(0, 1))
        assert OffsetStrategy.does_from_pivot_use_perpendicular_mode(edge, Vector(0, -1))

        edge = stretch.query_edges(Point(2, 0.5))[0]
        assert edge.shape.equals(LineString([(2, 0), (2, 1)]))
        assert not OffsetStrategy.does_from_pivot_use_perpendicular_mode(edge, Vector(0.2, 0))
        assert not OffsetStrategy.does_from_pivot_use_perpendicular_mode(edge, Vector(-0.2, 0))

    def test_does_from_pivot_use_perpendicular_mode_case1(self, stretch_of_single_box):
        stretch = stretch_of_single_box
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (2, 0)]))
        assert not OffsetStrategy.does_from_pivot_use_perpendicular_mode(edge, Vector(0, 0.5))

    def test_does_to_pivot_use_perpendicular_mode(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (2, 0)]))
        assert not OffsetStrategy.does_to_pivot_use_perpendicular_mode(edge, Vector(0, 1))
        assert OffsetStrategy.does_to_pivot_use_perpendicular_mode(edge, Vector(0, -1))

        edge = stretch.query_edges(Point(2, 0.5))[0]
        assert edge.shape.equals(LineString([(2, 0), (2, 1)]))
        assert not OffsetStrategy.does_to_pivot_use_perpendicular_mode(edge, Vector(0.2, 0))
        assert OffsetStrategy.does_to_pivot_use_perpendicular_mode(edge, Vector(-0.2, 0))

    def test_offset_from_pivot_case0(self, stretch_of_single_box):
        stretch = stretch_of_single_box
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (2, 0)]))
        assert len(stretch.pivots) == 4

        # since vector is pointing downward, not on the left of edge's direction, thus shrinking closure should be None
        pivot = (OffsetStrategy(edge, Vector(0, -1))
                 .offset_from_pivot(edge, Vector(0, -1), None))
        assert pivot.shape.equals(Point(0, -1))
        assert len(stretch.pivots) == 5

    def test_offset_from_pivot_case1(self, stretch_of_single_box):
        stretch = stretch_of_single_box
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (2, 0)]))
        assert len(stretch.pivots) == 4

        # since vector is pointing upward, on the left of edge's direction, thus thrinking closure should be the one
        # related to current edge
        pivot = (OffsetStrategy(edge, Vector(0, 0.5))
                 .offset_from_pivot(edge, Vector(0, 0.5), stretch.closure_snapshot().closures[0]))
        assert pivot.shape.equals(Point(0, 0.5))
        assert len(stretch.pivots) == 5

    def test_offset_to_pivot_case0(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = stretch.query_edges(Point(2, 0.5))[0]
        assert edge.shape.equals(LineString([(2, 0), (2, 1)]))

        closures = sorted(stretch.closure_snapshot().closures, key=lambda closure: closure.shape.area)
        closure = closures[1]

        origin_num_pivots = len(stretch.pivots)
        origin_num_edges = len(stretch.edges)

        pivot = (OffsetStrategy(edge, Vector(-0.5, 0))
                 .offset_to_pivot(edge, Vector(-0.5, 0), closure))

        assert pivot.shape.equals(Point(1.5, 1))
        assert len(stretch.pivots) == origin_num_pivots + 1
        assert len(stretch.edges) == origin_num_edges + 2  # add edge and its reverse

    def test_do_offset_case0(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = stretch.edges[0]
        assert edge.shape.equals(LineString([(0, 0), (2, 0)]))

        origin_num_pivots = len(stretch.pivots)

        OffsetStrategy(edge, Vector(0, -1)).do()
        assert len(stretch.pivots) == origin_num_pivots + 2
        assert len(stretch.edges) == 11

        closures = sorted(stretch.closure_snapshot().closures, key=lambda closure: closure.shape.area)
        assert len(closures) == 2
        assert closures[1].shape.equals(box(0, -1, 2, 2))
        assert closures[0].shape.equals(box(2, 0, 3, 1))

    def test_do_offset_case1(self, stretch_of_two_box):
        stretch = stretch_of_two_box
        edge = stretch.query_edges(Point(2, 0.5))[0]
        assert edge.shape.equals(LineString([(2, 0), (2, 1)]))

        origin_num_pivots = len(stretch.pivots)

        OffsetStrategy(edge, Vector(-1, 0)).do()
        assert len(stretch.pivots) == origin_num_pivots + 2
        assert len(stretch.edges) == 12

        closures = sorted(stretch.closure_snapshot().closures, key=lambda closure: closure.shape.area)
        assert len(closures) == 2
        assert closures[1].shape.equals(loads('POLYGON ((1 0, 1 1, 2 1, 2 2, 0 2, 0 0, 1 0))'))
        assert closures[0].shape.equals(loads('POLYGON ((3 0, 3 1, 2 1, 1 1, 1 0, 2 0, 3 0))'))

    def test_offset_corner_case(self, stretch_of_single_box):
        stretch0 = stretch_of_single_box
        edge = stretch0.edges[0]
        with pytest.raises(ValueError):
            OffsetStrategy(edge, Vector(0, 3)).do()

        edge = stretch0.edges[0]
        with pytest.raises(ValueError):
            OffsetStrategy(edge, Vector(1, 0)).do()

    def test_offset_for_pivot_attaching_mode_in_hard_case(self, stretch_for_offset):
        stretch = stretch_for_offset
        edge = stretch.edges[0]
        OffsetStrategy(edge, Vector(0, -1 - MATH_EPS)).do()
        closures = stretch.closure_snapshot().closures
        assert len(closures) == 2
