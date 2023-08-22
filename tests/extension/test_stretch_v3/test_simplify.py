import pytest

from shapely.extension.model.stretch.stretch_v3 import Edge
from shapely.geometry import LinearRing, Point, LineString


class TestSimplify:
    def test_simplify_closure(self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure
        closure = stretch.closures[0]
        another_closure = stretch.closures[1]

        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12
        assert len(closure.exterior) == 6
        assert len(another_closure.exterior) == 6

        closure.simplify()

        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert len(closure.exterior) == 4
        assert closure.exterior.shape.equals(LinearRing([(0, 0), (30, 0), (30, 20), (0, 20)]))

        assert len(another_closure.exterior) == 4
        assert another_closure.exterior.shape.equals(LinearRing([(0, 0), (0, -10), (30, -10), (30, 0)]))

    def test_simplify_closure_interior(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10
        assert len(stretch.closures) == 1

        closure = stretch.closures[0]
        assert len(closure.interiors) == 1
        interior = closure.interiors[0]
        assert len(interior) == 6

        closure.simplify()

        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 1

        assert len(closure.interiors) == 1
        interior = closure.interiors[0]
        assert len(interior) == 4
        assert interior.shape.equals(LinearRing([(5, 25), (25, 25), (25, 20), (5, 20)]))

    def test_simplify_stretch(self, stretch_exterior_offset_hit_out_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_out_with_reverse_closure
        shapes = [c.shape for c in stretch.closures]

        stretch.simplify()
        assert len(stretch.closures) == 2
        assert stretch.closures[0].shape.equals(shapes[0])
        assert not stretch.closures[0].shape.almost_equals(shapes[0])
        assert stretch.closures[1].shape.equals(shapes[1])
        assert not stretch.closures[1].shape.almost_equals(shapes[1])

    def test_cargo_after_simplify_using_default_strategy(self, stretch_box_duplicate_pivots):
        stretch = stretch_box_duplicate_pivots

        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert len(stretch.closures) == 1

        stretch.edge('(0,4)').cargo['test'] = 0
        stretch.edge('(4,1)').cargo['test'] = 1

        stretch.simplify(consider_cargo_equality=False)

        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        edges = stretch.edges_by_query(Point(0.3, 0))
        assert len(edges) == 1
        assert edges[0].cargo['test'] == 0
        assert edges[0].shape.equals(LineString([(0, 0), (1, 0)]))

    def test_cargo_after_simplify_using_long_edge_inherit(self, stretch_box_duplicate_pivots):
        stretch = stretch_box_duplicate_pivots

        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert len(stretch.closures) == 1

        stretch.edge('(0,4)').cargo['test'] = 0
        stretch.edge('(4,1)').cargo['test'] = 1

        def long_edge_inherit(edge0: Edge, edge1: Edge):
            if edge0.shape.length > edge1.shape.length:
                return edge0
            return edge1

        stretch.simplify(consider_cargo_equality=False, cargo_target=long_edge_inherit)

        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        edges = stretch.edges_by_query(Point(0.3, 0))
        assert len(edges) == 1
        assert edges[0].cargo['test'] == 1
        assert edges[0].shape.equals(LineString([(0, 0), (1, 0)]))

    def test_simplify_stretch_with_cut(self, stretch_2_boxes):
        """
        ┌─────────────────────┬─────────────────────┐
        │                     │                     │
        │                     │                     │
        │                     │                     │
        │           ──────────┤                     │
        │                     │                     │
        │                     │                     │
        │                     │                     │
        └─────────────────────┴─────────────────────┘
        Parameters
        ----------
        stretch_2_boxes

        Returns
        -------

        """
        stretch = stretch_2_boxes
        stretch.add_pivot(Point(1, 0.5))
        assert len(stretch.edges) == 10
        stretch.simplify()
        assert len(stretch.edges) == 8

        stretch.closures[0].cut(LineString([(0.5, 0.5), (1.5, 0.5)]))
        assert len(stretch.edges) == 12
        assert sum(map(lambda closure: closure.shape.area, stretch.closures)) == pytest.approx(2.0)
        stretch.simplify()

        assert sum(map(lambda closure: closure.shape.area, stretch.closures)) == pytest.approx(2.0)
        assert len(stretch.edges) == 12
