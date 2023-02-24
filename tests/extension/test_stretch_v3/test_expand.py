import pytest

from shapely.extension.model.stretch.stretch_v3 import Pivot, EdgeSeq
from shapely.geometry import Point, LineString, LinearRing, Polygon


class TestExpand:
    def test_expand_edge_by_mid_piont(self, stretch_4_dangling_edge):
        stretch = stretch_4_dangling_edge
        pivot = stretch.create_pivot(Point(0.5, 0))
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 4

        edge = stretch.edge('(0,1)')
        edge_seq = edge.expand().by(pivot)
        assert len(edge_seq) == 2
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert len(pivot.in_edges) == 1
        assert len(pivot.out_edges) == 1

    def test_expand_edge_and_reverse_edge_by_mid_point(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        pivot = stretch.create_pivot(Point(1, 0.5))
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 2

        sharing_edge = stretch.edge('(1,2)')
        assert sharing_edge.shape.equals(LineString([(1, 0), (1, 1)]))
        edge_seq = sharing_edge.expand().by(pivot)
        assert len(edge_seq) == 2
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 10
        assert len(stretch.closures) == 2
        assert len(stretch.closures[0].exterior) == 5
        assert len(stretch.closures[1].exterior) == 5

    def test_expand_edge_by_from_pivot(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        pivot = stretch.create_pivot(Point(1, 0.5))
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 8

        edge = stretch.edge('(1,2)')
        edge_seq = edge.expand().by(stretch.pivot('1'))
        assert len(edge_seq) == 1
        assert edge_seq[0] is stretch.edge('(1,2)')
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 8

        edge.expand().by([stretch.pivot('1'), stretch.pivot('2')])
        assert len(edge_seq) == 1
        assert edge_seq[0] is stretch.edge('(1,2)')
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 8

        with pytest.raises(ValueError):
            edge.expand().by([pivot, stretch.pivot('1'), stretch.pivot('2')])

    def test_expand_edge_by_pivots_that_are_not_all_endpoints_of_edge(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        pivot = stretch.create_pivot(Point(1, 0.5))
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 8

        edge = stretch.edge('(1,2)')
        edge_seq = edge.expand().by([stretch.pivot('1'), pivot, stretch.pivot('2')])
        assert len(edge_seq) == 2

    def test_expand_closure_exterior_by_pivot(self, stretch_box):
        edge = stretch_box.edge('(0,1)')
        pivot = stretch_box.create_pivot(Point(0.5, 0))
        assert len(stretch_box.pivots) == 5
        assert len(stretch_box.edges) == 4

        edge_seq = edge.expand().by(pivot)
        assert len(edge_seq) == 2
        assert len(stretch_box.pivots) == 5
        assert len(stretch_box.edges) == 5

    def test_expand_closure_interior_by_pivot(self, stretch_box_holes):
        stretch = stretch_box_holes
        edge = stretch.edge('(5,4)')
        pivot = stretch.create_pivot(Point(2.5, 2.1))
        assert len(stretch.pivots) == 13
        assert len(stretch.edges) == 12

        edge_seq = edge.expand().by(pivot)
        assert len(edge_seq) == 2
        assert len(stretch.pivots) == 13
        assert len(stretch.edges) == 13
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').interiors[0]) == 5
        assert stretch.closure('0').interiors[0].shape.equals(
            LinearRing([(2, 2), (2, 3), (3, 3), (3, 2), (2.5, 2.1), (2, 2)]))

    def test_expand_closure_exterior_by_edge(self, stretch_box):
        stretch = stretch_box
        pivot0 = stretch.create_pivot(Point(2, 0))
        pivot1 = stretch.create_pivot(Point(2, 1))
        new_edge = stretch.create_edge().from_pivot(pivot0).to_pivot(pivot1).create()

        edge = stretch.edge('(1,2)')
        edge_seq = edge.expand().by(new_edge)
        assert len(edge_seq) == 3
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 6
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').exterior) == 6
        assert stretch.closure('0').shape.equals(Polygon([(0, 0), (1, 0), (2, 0), (2, 1), (1, 1), (0, 1)]))
        assert len(stretch.pivot('1').in_edges) == 1
        assert len(stretch.pivot('1').out_edges) == 1
        assert len(stretch.pivot('2').in_edges) == 1
        assert len(stretch.pivot('2').out_edges) == 1

    def test_expand_sharing_edge_of_2_closures_by_edge(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        pivot0 = stretch.create_pivot(Point(1.1, 0.5))
        pivot1 = stretch.create_pivot(Point(1.1, 0.6))
        new_edge = stretch.create_edge().from_pivot(pivot0).to_pivot(pivot1).create()

        edge = stretch.edge('(1,2)')
        edge_seq = edge.expand().by(new_edge)
        for _edge in edge_seq:
            assert _edge.reverse is not None

        assert len(edge_seq) == 3
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12
        assert len(stretch.closures) == 2
        assert stretch.closure('0').shape.equals(
            Polygon([(0, 0), (1, 0), (1.1, 0.5), (1.1, 0.6), (1, 1), (0, 1)]))
        assert stretch.closure('1').shape.equals(
            Polygon([(1, 0), (2, 0), (2, 1), (1, 1), (1.1, 0.6), (1.1, 0.5), (1, 0)]))

    def test_expand_closure_interior_by_edge(self, stretch_box_holes):
        stretch = stretch_box_holes
        pivot0 = stretch.create_pivot(Point(4, 4))
        pivot1 = stretch.create_pivot(Point(4, 3))
        new_edge = stretch.create_edge().from_pivot(pivot0).to_pivot(pivot1).create()

        edge = stretch.edge('(6,5)')
        edge_seq = edge.expand().by(new_edge)
        assert len(edge_seq) == 3
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').interiors[0]) == 6
        assert stretch.closure('0').interiors[0].shape.equals(
            LinearRing([(2, 2), (2, 3), (3, 3), (4, 4), (4, 3), (3, 2), (2, 2)]))

    def test_expand_closure_exterior_by_edge_seq(self, stretch_box):
        stretch = stretch_box
        pivot0 = stretch.create_pivot(Point(2, 0))
        pivot1 = stretch.create_pivot(Point(2, 1))
        pivot2 = stretch.create_pivot(Point(2, 2))
        edge_seq = Pivot.connect([pivot0, pivot1, pivot2])

        edge = stretch.edge('(1,2)')
        new_edge_seq = edge.expand().by(edge_seq)
        assert len(new_edge_seq) == 4
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 7
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').exterior) == 7
        assert stretch.closure('0').shape.equals(Polygon([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 1), (0, 1)]))

    def test_expand_closure_interior_by_edge_seq(self, stretch_box_holes):
        stretch = stretch_box_holes
        pivot0 = stretch.create_pivot(Point(4, 4))
        pivot1 = stretch.create_pivot(Point(4, 3))
        pivot2 = stretch.create_pivot(Point(4, 2))
        new_edge_seq = Pivot.connect([pivot0, pivot1, pivot2])

        edge = stretch.edge('(6,5)')
        edge_seq = edge.expand().by(new_edge_seq)
        assert len(edge_seq) == 4
        assert len(stretch.pivots) == 15
        assert len(stretch.edges) == 15
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').interiors[0]) == 7
        assert stretch.closure('0').interiors[0].shape.equals(
            LinearRing([(2, 2), (2, 3), (3, 3), (4, 4), (4, 3), (4, 2), (3, 2), (2, 2)]))

    def test_expand_sharing_edge_of_2_closures_by_edge_seq(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        pivot0 = stretch.create_pivot(Point(1.1, 0.5))
        pivot1 = stretch.create_pivot(Point(1.1, 0.6))
        pivot2 = stretch.create_pivot(Point(1.2, 0.7))
        new_edge_seq = Pivot.connect([pivot0, pivot1, pivot2])

        edge = stretch.edge('(1,2)')
        edge_seq = edge.expand().by(new_edge_seq)
        assert len(edge_seq) == 4
        assert len(stretch.pivots) == 9
        assert len(stretch.edges) == 14
        assert len(stretch.closures) == 2
        assert stretch.closure('0').shape.equals(
            Polygon([(0, 0), (1, 0), (1.1, 0.5), (1.1, 0.6), (1.2, 0.7), (1, 1), (0, 1)]))
        assert stretch.closure('1').shape.equals(
            Polygon([(1, 0), (2, 0), (2, 1), (1, 1), (1.2, 0.7), (1.1, 0.6), (1.1, 0.5), (1, 0)]))

    def test_cargo_inheritance_for_expand(self, stretch_2_boxes):
        stretch = stretch_2_boxes

        new_pivots = [
            Pivot(Point(1.1, 0.5), stretch, '6'),
            Pivot(Point(1.1, 0.6), stretch, '7'),
        ]
        stretch._pivot_map.update({p.id: p for p in new_pivots})
        stretch.shrink_id_gen()

        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 2

        edge12 = stretch.edge('(1,2)')
        edge21 = stretch.edge('(2,1)')

        edge12.cargo['test'] = 'edge12'
        edge21.cargo['test'] = 'edge21'

        stretch.pivot('1').cargo['test'] = 'pivot1'
        stretch.pivot('2').cargo['test'] = 'pivot2'

        stretch.closure('0').cargo['test'] = 'closure0'
        stretch.closure('1').cargo['test'] = 'closure1'

        result = edge12.expand().by(new_pivots)
        assert isinstance(result, EdgeSeq)
        assert len(result) == 3
        assert result[0].cargo['test'] == 'edge12'
        assert result[2].cargo['test'] == 'edge12'
        assert result[1].cargo.get('test') is None

        assert stretch.pivot('1').cargo['test'] == 'pivot1'
        assert stretch.pivot('2').cargo['test'] == 'pivot2'
        assert stretch.pivot('6').cargo.get('test') is None
        assert stretch.pivot('7').cargo.get('test') is None

        assert stretch.closure('0').cargo['test'] == 'closure0'
        assert stretch.closure('1').cargo['test'] == 'closure1'

        assert result[0].reverse.cargo['test'] == 'edge21'
        assert result[2].reverse.cargo['test'] == 'edge21'
        assert result[1].reverse.cargo.get('test') is None
