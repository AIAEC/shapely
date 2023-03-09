import json
from copy import deepcopy
from unittest import skip

from shapely.extension.model.stretch.stretch_v3 import Stretch
from shapely.geometry import Point


class TestBasicAttribute:
    def test_resource_relationship(self, stretch_box):
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 4
        assert len(stretch_box.closures) == 1

        closure = stretch_box.closures[0]
        assert all(pivot.stretch is stretch_box for pivot in stretch_box.pivots)
        assert all(edge.stretch is stretch_box for edge in stretch_box.edges)
        assert all(closure.stretch is stretch_box for closure in stretch_box.closures)

        assert all(edge.closure == closure for edge in stretch_box.edges)
        assert stretch_box.pivots[0].in_edges == [stretch_box.edges[3]]
        assert stretch_box.pivots[0].out_edges == [stretch_box.edges[0]]
        assert stretch_box.pivots[1].in_edges == [stretch_box.edges[0]]
        assert stretch_box.pivots[1].out_edges == [stretch_box.edges[1]]
        assert stretch_box.pivots[2].in_edges == [stretch_box.edges[1]]
        assert stretch_box.pivots[2].out_edges == [stretch_box.edges[2]]
        assert stretch_box.pivots[3].in_edges == [stretch_box.edges[2]]
        assert stretch_box.pivots[3].out_edges == [stretch_box.edges[3]]

    def test_resource_fetch(self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure

        assert stretch.pivot('0') is not None
        assert stretch.pivot('8') is None

        assert stretch.edge('(0,1)') is not None
        assert stretch.edge('(0,9)') is None

        assert stretch.closure('0') is not None
        assert stretch.closure('9') is None

        edge_seq = stretch.edge_seq(['0', '1', '2', '3'])
        assert edge_seq is not None
        assert len(edge_seq) == 3

    def test_dumps(self, stretch_for_closure_strategy):
        stretch = stretch_for_closure_strategy

        json_str = stretch.dumps()
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        obj = json.loads(json_str)
        assert isinstance(obj, dict)

    def test_dumps_with_cargo(self, stretch_box):
        stretch = stretch_box

        pivot = stretch.pivot('0')
        pivot.cargo['test'] = 'pivot'

        edge = stretch.edge('(0,1)')
        edge.cargo['test'] = 'edge'

        closure = stretch.closure('0')
        closure.cargo['test'] = 'closure'

        json_str = stretch.dumps()
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        obj = json.loads(json_str)
        assert isinstance(obj, dict)
        assert obj['pivot_cargo']['0'] == {'test': 'pivot'}
        assert obj['edge_cargo']['(0,1)'] == {'test': 'edge'}
        assert obj['closure_cargo']['0'] == {'test': 'closure'}

    def test_loads(self, stretch_for_closure_strategy):
        stretch = stretch_for_closure_strategy

        json_str = stretch.dumps()
        stretch2 = Stretch.loads(json_str)

        assert set(stretch2.pivots) == set(stretch.pivots)
        assert set(stretch2.edges) == set(stretch.edges)
        assert set(stretch2.closures) == set(stretch.closures)

    def test_loads_with_cargo(self, stretch_box):
        stretch = stretch_box

        pivot = stretch.pivot('0')
        pivot.cargo['test'] = 'pivot'

        edge = stretch.edge('(0,1)')
        edge.cargo['test'] = 'edge'

        closure = stretch.closure('0')
        closure.cargo['test'] = 'closure'

        json_str = stretch.dumps()
        stretch2 = Stretch.loads(json_str)

        assert set(stretch2.pivots) == set(stretch.pivots)
        assert set(stretch2.edges) == set(stretch.edges)
        assert set(stretch2.closures) == set(stretch.closures)

        assert stretch2.pivot('0').cargo.data == {'test': 'pivot'}
        assert stretch2.edge('(0,1)').cargo.data == {'test': 'edge'}
        assert stretch2.closure('0').cargo.data == {'test': 'closure'}

    @skip('skip drawing test for online unittest, only do it locally')
    def test_draw(self, stretch_for_closure_strategy):
        from shapely.extension.draw import Draw

        stretch = stretch_for_closure_strategy
        drawer = Draw()
        for closure in stretch.closures:
            drawer.draw(closure.shape, color=Draw.RANDOM, edge_color=Draw.BLACK)

        drawer.show()
