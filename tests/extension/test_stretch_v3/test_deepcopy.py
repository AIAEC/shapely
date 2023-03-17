from copy import deepcopy

from shapely.geometry import Point

from shapely.extension.model.stretch.stretch_v3 import Stretch


class TestDeepcopy:
    def test_deepcopy_default_cargo_dict(self):
        stretch = Stretch(default_pivot_cargo_dict={'a': 1}, default_edge_cargo_dict={'b': 2},
                          default_closure_cargo_dict={'c': 3})
        copy = deepcopy(stretch)
        assert copy._default_pivot_cargo_dict == {'a': 1}
        assert copy._default_edge_cargo_dict == {'b': 2}
        assert copy._default_closure_cargo_dict == {'c': 3}

    def test_deepcopy_of_stretch(self, stretch_box):
        stretch_box.pivots[0].cargo['test'] = 'pivot'
        stretch_box.edges[0].cargo['test'] = 'edge'
        stretch_box.closures[0].cargo['test'] = 'closure'

        stretch_box_deep_copy = deepcopy(stretch_box)

        assert len(stretch_box_deep_copy.pivots) == 4
        assert len(stretch_box_deep_copy.edges) == 4
        assert len(stretch_box_deep_copy.closures) == 1

        assert stretch_box_deep_copy.pivots[0].cargo['test'] == 'pivot'
        assert stretch_box_deep_copy.edges[0].cargo['test'] == 'edge'
        assert stretch_box_deep_copy.closures[0].cargo['test'] == 'closure'

        for pivot, pivot_deep_copy in zip(stretch_box.pivots, stretch_box_deep_copy.pivots):
            assert pivot is not pivot_deep_copy
            assert pivot_deep_copy.id == pivot.id
            assert pivot_deep_copy.origin == pivot.origin
            assert pivot_deep_copy.stretch is stretch_box_deep_copy

            for in_edge, in_edge_deep_copy in zip(pivot.in_edges, pivot_deep_copy.in_edges):
                assert in_edge_deep_copy is not in_edge
                assert in_edge.to_pivot is pivot
                assert in_edge_deep_copy.to_pivot is pivot_deep_copy

            for out_edge, out_edge_deep_copy in zip(pivot.out_edges, pivot_deep_copy.out_edges):
                assert out_edge_deep_copy is not out_edge
                assert out_edge.from_pivot is pivot
                assert out_edge_deep_copy.from_pivot is pivot_deep_copy

        for edge, edge_deep_copy in zip(stretch_box.edges, stretch_box_deep_copy.edges):
            assert edge is not edge_deep_copy
            assert edge_deep_copy.id == edge.id
            assert edge_deep_copy.stretch is stretch_box_deep_copy
            assert edge.to_pivot is not edge_deep_copy.to_pivot
            assert edge.from_pivot is not edge_deep_copy.from_pivot
            assert edge.closure is not edge_deep_copy.closure

        for closure, closure_deep_copy in zip(stretch_box.closures, stretch_box_deep_copy.closures):
            assert closure is not closure_deep_copy
            assert closure_deep_copy.id == closure.id
            assert closure.exterior is not closure_deep_copy.exterior
            assert closure.interiors is not closure_deep_copy.interiors
            assert closure_deep_copy.stretch is stretch_box_deep_copy

    def test_deepcopy_of_pivot(self, stretch_box):
        pivot = stretch_box.pivot('0')
        pivot.cargo['test'] = 'pivot'
        pivot_deep_copy = deepcopy(pivot)

        assert pivot_deep_copy.cargo['test'] == 'pivot'

        # deep copy is a different object from origin pivot
        pivot_deep_copy.origin = Point(10, 10)  # change deep copy's origin
        assert pivot.origin == Point(0, 0), 'deep copy should be separate instance from origin pivot'

        # deep copy is not in stretch, although it has the same id with origin pivot
        assert all(pivot_deep_copy is not _pivot for _pivot in stretch_box.pivots)
        assert len(stretch_box.pivots) == 4

        # edges still hold the origin pivot, not the deep copy
        for in_edge in pivot.in_edges:
            assert in_edge.to_pivot is not pivot_deep_copy
            assert in_edge.to_pivot is pivot

        for out_edge in pivot.out_edges:
            assert out_edge.from_pivot is not pivot_deep_copy
            assert out_edge.from_pivot is pivot

        # deep copy has back ref to the origin pivot's edges
        assert all(in_edge in pivot.in_edges for in_edge in pivot_deep_copy.in_edges)
        assert all(out_edge in pivot.out_edges for out_edge in pivot_deep_copy.out_edges)

        # deep copy has back ref to the same stretch as origin pivot
        assert pivot_deep_copy.stretch is pivot.stretch

    def test_deepcopy_of_edge(self, stretch_box):
        edge = stretch_box.edge('(0,1)')
        edge.cargo['test'] = 'edge'
        edge_deep_copy = deepcopy(edge)
        setattr(edge_deep_copy, '_test_mark', '0')

        # deepcopy should have same cargo
        assert edge_deep_copy.cargo['test'] == 'edge'

        # deepcopy of edge is not in stretch
        assert all(edge_deep_copy is not _edge for _edge in stretch_box.edges)
        assert getattr(edge, '_test_mark', None) != '0'

        # deepcopy of edge should hold deepcopy of pivots
        edge_deep_copy.from_pivot.origin = Point(10, 10)
        edge_deep_copy.to_pivot.origin = Point(11, 10)
        assert edge.from_pivot.origin == Point(0, 0)
        assert edge.to_pivot.origin == Point(1, 0)
        assert all(edge_deep_copy.from_pivot is not _pivot for _pivot in stretch_box.pivots)
        assert all(edge_deep_copy.to_pivot is not _pivot for _pivot in stretch_box.pivots)

        # the deepcopy pivot of deepcopy edge should have back ref to the deepcopy edge
        assert len(edge_deep_copy.from_pivot.out_edges) == 1
        assert edge_deep_copy.from_pivot.out_edges[0] is edge_deep_copy
        assert len(edge_deep_copy.to_pivot.in_edges) == 1
        assert edge_deep_copy.to_pivot.in_edges[0] is edge_deep_copy

        # deepcopy of edge should have back ref to the same closure as origin edge
        assert edge_deep_copy.closure is edge.closure

        # deepcopy of edge should have back ref to the same stretch as origin edge
        assert edge_deep_copy.stretch is edge.stretch

    def test_deepcopy_of_edge_seq(self, stretch_box):
        edge_seq = stretch_box.closure('0').exterior
        edge_seq_deep_copy = deepcopy(edge_seq)
        for edge, edge_copy in zip(edge_seq, edge_seq_deep_copy):
            assert edge is not edge_copy
            assert edge.from_pivot is not edge_copy.from_pivot
            assert edge.to_pivot is not edge_copy.to_pivot

    def test_deepcopy_of_closure(self, stretch_box):
        closure = stretch_box.closure('0')
        closure.cargo['test'] = 'closure'
        closure_deep_copy = deepcopy(closure)
        closure_deep_copy._id = '1'

        # closure copy should have same cargo
        assert closure_deep_copy.cargo['test'] == 'closure'

        # closure copy should be a different object from origin closure
        assert len(stretch_box.closures) == 1
        assert closure.id == '0'
        assert all(closure_deep_copy is not _closure for _closure in stretch_box.closures)

        # closure copy should have deepcopy edges and pivots instead of the origin edges and pivots
        for edge, edge_copy in zip(closure.exterior, closure_deep_copy.exterior):
            assert edge is not edge_copy
            assert edge.from_pivot is not edge_copy.from_pivot
            assert edge.to_pivot is not edge_copy.to_pivot
            assert edge.closure is closure
            assert edge_copy.closure is closure_deep_copy

            assert edge_copy.from_pivot.out_edges[0] is edge_copy
            assert edge_copy.to_pivot.in_edges[0] is edge_copy

    def test_deepcopy_dangling_edge(self, stretch_8_dangling_edges):
        stretch = stretch_8_dangling_edges
        assert len(stretch.edges) == 8
        assert len(stretch.pivots) == 8
        assert len(stretch.closures) == 0

        stretch_copy = deepcopy(stretch)
        assert stretch_copy is not stretch
        assert len(stretch_copy.edges) == 8
        assert len(stretch_copy.pivots) == 8
        assert len(stretch_copy.closures) == 0
