from shapely.extension.model.stretch.stretch_v3 import Stretch, EdgeSeq
from shapely.geometry import Point, Polygon


class TestLowLevelCreation:
    def test_create_pivot(self):
        stretch = Stretch()
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0

        pivot = stretch.create_pivot((0, 0))
        assert len(stretch.pivots) == 1
        assert pivot in stretch.pivots
        assert pivot.id in stretch._pivot_map
        assert pivot.id == '0'
        assert pivot.shape == Point(0, 0)
        assert pivot.in_edges == []
        assert pivot.out_edges == []

        pivot = stretch.create_pivot((1, 1))
        assert len(stretch.pivots) == 2
        assert pivot in stretch.pivots
        assert pivot.id in stretch._pivot_map
        assert pivot.id == '1'
        assert pivot.shape == Point(1, 1)
        assert pivot.in_edges == []
        assert pivot.out_edges == []

        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

    def test_create_edge_without_duplicate(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

        edge = stretch.create_edge().from_pivot_by_id('0').to_pivot_by_id('1').create()
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 1
        assert len(stretch.closures) == 0
        assert edge in stretch.edges
        assert edge.id in stretch._edge_map
        assert edge.id == '(0,1)'
        assert edge.closure is None
        assert stretch.pivot('0').out_edges == [edge]
        assert not stretch.pivot('0').in_edges
        assert stretch.pivot('1').in_edges == [edge]
        assert not stretch.pivot('1').out_edges

    def test_create_edge_with_duplicate(self, stretch_box_holes):
        stretch = stretch_box_holes
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        outer_edge = stretch.create_edge().from_pivot_by_id('0').to_pivot_by_id('1').create()
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert outer_edge in stretch.edges
        assert outer_edge.id in stretch._edge_map
        assert outer_edge.id == '(0,1)'
        assert outer_edge.closure is not None
        assert stretch.pivot('0').out_edges == [outer_edge]
        assert len(stretch.pivot('0').in_edges) == 1
        assert stretch.pivot('1').in_edges == [outer_edge]
        assert len(stretch.pivot('1').out_edges) == 1

        inner_edge = stretch.create_edge().from_pivot_by_id('7').to_pivot_by_id('6').create()
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert inner_edge in stretch.edges
        assert inner_edge.id in stretch._edge_map
        assert inner_edge.id == '(7,6)'
        assert inner_edge.closure is not None
        assert stretch.pivot('7').out_edges == [inner_edge]
        assert len(stretch.pivot('7').in_edges) == 1
        assert stretch.pivot('6').in_edges == [inner_edge]
        assert len(stretch.pivot('6').out_edges) == 1

    def test_create_closure_with_holes(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

        exterior_seq = EdgeSeq([stretch.create_edge().from_pivot_by_id('0').to_pivot_by_id('1').create(),
                                stretch.create_edge().from_pivot_by_id('1').to_pivot_by_id('2').create(),
                                stretch.create_edge().from_pivot_by_id('2').to_pivot_by_id('3').create(),
                                stretch.create_edge().from_pivot_by_id('3').to_pivot_by_id('0').create()])
        interior_seq = EdgeSeq([stretch.create_edge().from_pivot_by_id('7').to_pivot_by_id('6').create(),
                                stretch.create_edge().from_pivot_by_id('6').to_pivot_by_id('5').create(),
                                stretch.create_edge().from_pivot_by_id('5').to_pivot_by_id('4').create(),
                                stretch.create_edge().from_pivot_by_id('4').to_pivot_by_id('7').create()])
        closure = stretch.create_closure().exterior(exterior_seq).add_interior(interior_seq).create()
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 1
        assert closure in stretch.closures
        assert closure.id in stretch._closure_map
        assert closure.id == '0'
        assert closure.exterior == exterior_seq
        assert closure.interiors == [interior_seq]
        assert closure.exterior.closure == closure
        assert closure.interiors[0].closure == closure
        assert closure.shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)], [[(1, 1), (2, 1), (2, 2), (1, 2)]]))

    def test_create_same_closure_twice(self, stretch_4_dangling_edge):
        stretch = stretch_4_dangling_edge
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 0

        edge_seq = EdgeSeq(stretch.edges)
        closure = stretch.create_closure().exterior(edge_seq).create()
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert closure in stretch.closures
        assert closure.id in stretch._closure_map
        assert closure.id == '0'
        assert closure.exterior == edge_seq
        assert closure.interiors == []
        assert closure.exterior.closure == closure
        assert closure.shape.equals(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))

        new_closure = stretch.create_closure().exterior(edge_seq).create()
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert new_closure in stretch.closures
        assert new_closure.id in stretch._closure_map
        assert new_closure.id == '0'
        assert closure is new_closure
