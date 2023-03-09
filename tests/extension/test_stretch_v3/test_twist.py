import pytest

from shapely.extension.model.stretch.stretch_v3 import Edge
from shapely.geometry import Polygon
from shapely.wkt import loads


class TestTwist:
    def test_twist_consecutive_edges_of_same_closure(self, stretch_box):
        stretch = stretch_box

        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        old_edges = stretch.edges[:2]
        edge = Edge.twist(*old_edges)
        assert isinstance(edge, Edge)
        assert edge in stretch.edges
        assert stretch.edge(edge.id) is edge
        assert all(old_edge not in stretch.edges for old_edge in old_edges)

        assert len(stretch.pivots) == 3
        assert stretch.pivot('1') is None
        assert len(stretch.edges) == 3
        assert len(stretch.closures) == 1
        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (1, 1), (0, 1)]))

    def test_twist_consecutive_edges_with_no_closure_attached(self, stretch_8_dangling_edges):
        stretch = stretch_8_dangling_edges

        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 0

        old_edges = stretch.edges[:2]
        edge = Edge.twist(*old_edges)
        assert isinstance(edge, Edge)
        assert edge in stretch.edges
        assert stretch.edge(edge.id) is edge
        assert all(old_edge not in stretch.edges for old_edge in old_edges)

        assert len(stretch.pivots) == 7
        assert stretch.pivot('1') is None
        assert len(stretch.edges) == 7
        assert len(stretch.closures) == 0

    def test_twist_back_and_force_edges(self, stretch_back_and_forth_edge_seq):
        stretch = stretch_back_and_forth_edge_seq

        edge0 = stretch.edge('(0,1)')
        edge1 = stretch.edge('(1,0)')

        with pytest.raises(ValueError):
            Edge.twist(edge0, edge1)

        assert edge0 in stretch.edges
        assert edge1 in stretch.edges

    def test_twist_consecutive_edges_in_same_interior(self, stretch_box_holes):
        stretch = stretch_box_holes
        edge0 = stretch.edge('(6,5)')
        edge1 = stretch.edge('(5,4)')
        assert edge0 in stretch.edges
        assert edge1 in stretch.edges
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2

        edge = Edge.twist(edge0, edge1)
        assert isinstance(edge, Edge)
        assert edge in stretch.edges
        assert stretch.edge(edge.id) is edge

        assert edge0 not in stretch.edges
        assert edge1 not in stretch.edges
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0), (2 2, 2 3, 3 3, 2 2), (9 6, 9 5, 8 5, 8 6, 9 6))'))

    def test_twist_consecutive_edges_with_reverse_closure(self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure

        edge0 = stretch.edge('(0,1)')
        edge1 = stretch.edge('(1,2)')
        assert edge0 in stretch.edges
        assert edge1 in stretch.edges
        assert len(stretch.closures) == 2
        assert len(stretch.edges) == 12
        assert len(stretch.pivots) == 8

        edge = Edge.twist(edge0, edge1)
        assert isinstance(edge, Edge)
        assert edge in stretch.edges
        assert stretch.edge(edge.id) is edge
        assert edge.from_pivot is stretch.pivot('0')
        assert edge.to_pivot is stretch.pivot('2')

        assert edge0 not in stretch.edges
        assert edge1 not in stretch.edges
        assert len(stretch.closures) == 2
        assert len(stretch.edges) == 10
        assert len(stretch.pivots) == 7
        assert stretch.pivot('1') is None

        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (20, 0), (30, 0), (30, 20), (0, 20)]))
        assert stretch.closures[1].shape.equals(Polygon([(0, 0), (0, -10), (30, -10), (30, 0), (20, 0)]))

    def test_twist_edges_negative_case(self, stretch_box):
        stretch = stretch_box

        edge0 = stretch.edges[0]
        edge1 = stretch.edges[2]

        with pytest.raises(ValueError):
            Edge.twist(edge0, edge1)

    def test_cargo_of_twist_edges(self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure

        edge12 = stretch.edge('(1,2)')
        edge21 = stretch.edge('(2,1)')
        edge32 = stretch.edge('(3,2)')

        edge12.cargo['test'] = 'edge12'
        edge21.cargo['test'] = 'edge21'
        edge32.cargo['test'] = 'edge32'

        stretch.pivot('1').cargo['test'] = 'pivot1'
        stretch.pivot('2').cargo['test'] = 'pivot2'
        stretch.pivot('3').cargo['test'] = 'pivot3'

        stretch.closure('0').cargo['test'] = 'closure0'
        stretch.closure('1').cargo['test'] = 'closure1'

        edge = Edge.twist(edge12, stretch.edge('(2,3)'))
        assert isinstance(edge, Edge)
        assert edge.cargo['test'] == 'edge12'
        assert edge.reverse.cargo['test'] == 'edge21'
        assert stretch.pivot('1').cargo['test'] == 'pivot1'
        assert stretch.pivot('2') is None
        assert stretch.pivot('3').cargo['test'] == 'pivot3'
        assert stretch.closure('0').cargo['test'] == 'closure0'
        assert stretch.closure('1').cargo['test'] == 'closure1'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert closures[0].shape.equals(loads('POLYGON ((0 0, 0 -10, 30 -10, 30 0, 10 0, 0 0))'))
        assert closures[1].shape.equals(loads('POLYGON ((0 0, 10 0, 30 0, 30 20, 0 20, 0 0))'))

