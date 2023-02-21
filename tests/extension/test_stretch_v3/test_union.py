from shapely.geometry import Polygon
from shapely.wkt import loads


class TestUnion:
    def test_union_2_joint_closure(self, stretch_2_disjoint_boxes):
        stretch = stretch_2_disjoint_boxes
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        closure0 = stretch.closure('0')
        closure1 = stretch.closure('1')

        result = closure0.union(closure1)
        assert len(result) == 2
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        assert result[0] is stretch.closure('0')
        assert all(edge.closure is result[0] for edge in result[0].edges)

        assert result[1] is stretch.closure('1')
        assert all(edge.closure is result[1] for edge in result[1].edges)

    def test_union_adjacent_boxes(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8

        closure0 = stretch.closure('0')
        closure1 = stretch.closure('1')

        result = closure0.union(closure1)
        assert len(result) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 6
        assert all(edge.closure is result[0] for edge in result[0].edges)

        assert stretch.closure('0') is None
        assert stretch.closure('1') is None
        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1), (0, 0)]))

    def test_union_adjacent_concave_boxes(self, stretch_with_2_adjacent_concave_boxes):
        stretch = stretch_with_2_adjacent_concave_boxes
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 16
        assert len(stretch.closures) == 2

        closures = stretch.closures
        result = closures[0].union(closures[1])
        assert len(result) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert len(stretch.closures) == 1
        assert all(edge.closure is result[0] for edge in result[0].edges)

        closure = stretch.closures[0]
        assert closure.shape.equals(loads(
            'POLYGON ((0 0, 1 0, 2 0, 2 1, 1 1, 0 1, 0 0), (1.2 0.7, 1.2 0.3, 1 0.3, 0.8 0.3, 0.8 0.7, 1 0.7, 1.2 0.7))'))
        assert len(closure.interiors) == 1
        assert closure.interiors[0].shape.equals(
            loads('LINESTRING (1.2 0.7, 1.2 0.3, 1 0.3, 0.8 0.3, 0.8 0.7, 1 0.7, 1.2 0.7)'))

    def test_union_outer_closure_and_inner_closure(self, stretch_outer_and_inner_closures):
        stretch = stretch_outer_and_inner_closures
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12
        assert len(stretch.closures) == 2

        closures = stretch.closures
        result = closures[0].union(closures[1])
        assert len(result) == 1
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert all(edge.closure is result[0] for edge in result[0].edges)

        closure = stretch.closures[0]
        assert closure.shape.equals(Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]))
        assert len(closure.interiors) == 0
