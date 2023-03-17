from random import shuffle

import pytest

from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
from shapely.extension.model.stretch.stretch_v3 import Edge
from shapely.extension.util.iter_util import win_slice


class TestClosureStrategy:
    def test_consecutive(self, stretch_for_closure_strategy):
        stretch = stretch_for_closure_strategy
        edge = stretch.edge('(0,1)')
        edge_seq = ClosureStrategy.consecutive_edges(edge)
        assert len(edge_seq) == 4
        assert edge_seq.closed
        assert edge_seq.closure is stretch.closure('0')
        assert edge_seq.closure.exterior == edge_seq

        edge = stretch.edge('(6,5)')
        edge_seq = ClosureStrategy.consecutive_edges(edge)
        assert len(edge_seq) == 11
        assert edge_seq.closed
        assert edge_seq.closure is stretch.closure('0')
        assert edge_seq.closure.interiors[0] == edge_seq

        edge = stretch.edge('(5,6)')
        edge_seq = ClosureStrategy.consecutive_edges(edge)
        assert len(edge_seq) == 5
        assert edge_seq.closed
        assert edge_seq.closure is stretch.closure('1')
        assert edge_seq.closure.exterior == edge_seq

        edge = stretch.edge('(11,10)')
        edge_seq = ClosureStrategy.consecutive_edges(edge)
        assert len(edge_seq) == 7
        assert edge_seq.closed
        assert edge_seq.closure is stretch.closure('2')
        assert edge_seq.closure.exterior == edge_seq

        edge = stretch.edge('(7,13)')
        edge_seq = ClosureStrategy.consecutive_edges(edge)
        assert len(edge_seq) == 6
        assert edge_seq.closed
        assert edge_seq.closure is stretch.closure('3')
        assert edge_seq.closure.exterior == edge_seq

        edge = stretch.edge('(18,17)')
        edge_seq = ClosureStrategy.consecutive_edges(edge)
        assert len(edge_seq) == 12
        assert edge_seq.closed
        assert edge_seq.closure is stretch.closure('4')
        assert edge_seq.closure.exterior == edge_seq

    def test_consecutive_of_seq_of_back_and_forth_edges(self, stretch_back_and_forth_edge_seq):
        stretch = stretch_back_and_forth_edge_seq
        edge = stretch.edge('(0,1)')
        edge_seq = ClosureStrategy.consecutive_edges(edge)
        assert len(edge_seq) == 4
        assert edge_seq.closed
        assert edge_seq[0] is stretch.edge('(0,1)')
        assert edge_seq[1] is stretch.edge('(1,2)')
        assert edge_seq[2] is stretch.edge('(2,1)')
        assert edge_seq[3] is stretch.edge('(1,0)')

    def test_consecutive_seq_when_given_candidates(self, stretch_box):
        stretch = stretch_box

        edge = stretch.edge('(0,1)')
        edge_seq = ClosureStrategy.consecutive_edges(edge,
                                                     candidate_edges={stretch.edge('(1,2)'), stretch.edge('(0,1)')})
        assert len(edge_seq) == 2
        assert not edge_seq.closed
        assert edge_seq[0] is stretch.edge('(0,1)')
        assert edge_seq[1] is stretch.edge('(1,2)')

    def test_consecutive_seq_when_given_empty_candidates(self, stretch_box):
        stretch = stretch_box

        edge = stretch.edge('(0,1)')
        edge_seq = ClosureStrategy.consecutive_edges(edge, candidate_edges=set())
        assert len(edge_seq) == 0
        assert not edge_seq.closed

    def test_consecutive_seq_when_given_candidates_not_include_self(self, stretch_box):
        stretch = stretch_box

        edge = stretch.edge('(0,1)')
        edge_seq = ClosureStrategy.consecutive_edges(edge, candidate_edges={stretch.edge('(1,2)')})
        assert len(edge_seq) == 0
        assert not edge_seq.closed

    def test_next(self, stretch_for_closure_strategy):
        stretch = stretch_for_closure_strategy
        next_ = stretch.edge('(15,7)').next(ClosureStrategy)
        assert next_ is stretch.edge('(7,16)')

        next_ = stretch.edge('(16,7)').next(ClosureStrategy)
        assert next_ is stretch.edge('(7,13)')

    def test_next_on_sequence_of_back_and_forth_edges(self, stretch_back_and_forth_edge_seq):
        stretch = stretch_back_and_forth_edge_seq
        next_ = stretch.edge('(0,1)').next(ClosureStrategy)
        assert next_ is stretch.edge('(1,2)')

        next_ = stretch.edge('(1,2)').next(ClosureStrategy)
        assert next_ is stretch.edge('(2,1)')

        next_ = stretch.edge('(2,1)').next(ClosureStrategy)
        assert next_ is stretch.edge('(1,0)')

        next_ = stretch.edge('(1,0)').next(ClosureStrategy)
        assert next_ is stretch.edge('(0,1)')

    def test_prev(self, stretch_for_closure_strategy):
        stretch = stretch_for_closure_strategy
        prev = stretch.edge('(10,11)').prev(ClosureStrategy)
        assert prev is stretch.edge('(6,10)')

        prev = stretch.edge('(10,12)').prev(ClosureStrategy)
        assert prev is stretch.edge('(11,10)')

    def test_prev_on_sequence_of_back_and_forth_edges(self, stretch_back_and_forth_edge_seq):
        stretch = stretch_back_and_forth_edge_seq
        prev = stretch.edge('(1,0)').prev(ClosureStrategy)
        assert prev is stretch.edge('(2,1)')

        prev = stretch.edge('(2,1)').prev(ClosureStrategy)
        assert prev is stretch.edge('(1,2)')

        prev = stretch.edge('(1,2)').prev(ClosureStrategy)
        assert prev is stretch.edge('(0,1)')

        prev = stretch.edge('(0,1)').prev(ClosureStrategy)
        assert prev is stretch.edge('(1,0)')

    def test_sort_unchainable_edges(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots
        edges = [
            Edge('0', '1', stretch=stretch),
            Edge('1', '2', stretch=stretch),
            Edge('2', '3', stretch=stretch),
            Edge('4', '5', stretch=stretch),
            Edge('5', '6', stretch=stretch),
            Edge('6', '7', stretch=stretch),
        ]
        with pytest.raises(ValueError):
            ClosureStrategy.sort_edges_by_chain(edges)

        shuffle(edges)
        with pytest.raises(ValueError):
            ClosureStrategy.sort_edges_by_chain(edges)

    def test_sort_chainable_edges(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots
        edges = [Edge('2', '3', stretch=stretch),
                 Edge('1', '2', stretch=stretch),
                 Edge('3', '4', stretch=stretch)]
        sorted_edges = ClosureStrategy.sort_edges_by_chain(edges)
        assert len(sorted_edges) == 3
        assert sorted_edges[0] == edges[1]

        edges = [Edge('6', '7', stretch=stretch),
                 Edge('5', '6', stretch=stretch),
                 Edge('4', '5', stretch=stretch)]
        sorted_edges = ClosureStrategy.sort_edges_by_chain(edges)
        assert len(sorted_edges) == 3
        assert sorted_edges[0] == edges[-1]

    def test_sort_chainable_edges_with_special_id_order(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots
        edges = [Edge('2', '4', stretch=stretch),
                 Edge('3', '2', stretch=stretch)]
        sorted_edges = ClosureStrategy.sort_edges_by_chain(edges)
        assert len(sorted_edges) == 2
        assert sorted_edges[0] == edges[1]
        assert sorted_edges[1] == edges[0]

    def test_sort_loop_chain_of_edges(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots
        edges = [Edge('2', '3', stretch=stretch),
                 Edge('1', '2', stretch=stretch),
                 Edge('3', '0', stretch=stretch),
                 Edge('0', '1', stretch=stretch)]
        sorted_edges = ClosureStrategy.sort_edges_by_chain(edges)
        assert len(sorted_edges) == 4
        for edge, next_edge in win_slice(sorted_edges, win_size=2, tail_cycling=True):
            assert edge.to_pid == next_edge.from_pid

        edges = [Edge('7', '4', stretch=stretch),
                 Edge('5', '6', stretch=stretch),
                 Edge('4', '5', stretch=stretch),
                 Edge('6', '7', stretch=stretch)]
        sorted_edges = ClosureStrategy.sort_edges_by_chain(edges)
        assert len(sorted_edges) == 4
        for edge, next_edge in win_slice(sorted_edges, win_size=2, tail_cycling=True):
            assert edge.to_pid == next_edge.from_pid

    def test_sort_edges_belonging_to_2_closures(self, stretch_2_boxes):
        stretch = stretch_2_boxes

        edges = [stretch.edge('(1,4)'), stretch.edge('(0,1)')]

        assert edges[0].closure != edges[1].closure
        sorted_edges = ClosureStrategy.sort_edges_by_chain(edges)
        assert len(sorted_edges) == 2
        assert sorted_edges[0] is stretch.edge('(0,1)')
        assert sorted_edges[1] is stretch.edge('(1,4)')

    def test_sort_edges_of_back_and_forth(self, stretch_2_groups_dangling_edges):
        stretch = stretch_2_groups_dangling_edges

        edges = [
            stretch.edge('(2,1)'),
            stretch.edge('(0,1)'),
            stretch.edge('(1,4)'),
            stretch.edge('(1,2)'),
        ]

        sorted_edges = ClosureStrategy.sort_edges_by_chain(edges)
        assert len(sorted_edges) == 4

    def test_sort_edges_of_flower_cracks_which_form_closed_ring(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots

        edges = [
            Edge('0', '4', stretch=stretch),
            Edge('4', '7', stretch=stretch),
            Edge('7', '4', stretch=stretch),
            Edge('4', '6', stretch=stretch),
            Edge('6', '4', stretch=stretch),
            Edge('4', '5', stretch=stretch),
            Edge('5', '4', stretch=stretch),
            Edge('4', '0', stretch=stretch),
        ]

        for i in range(len(edges)):
            other_edges = edges[:i] + edges[i + 1:]
            shuffle(other_edges)
            composite_edges = [edges[i]] + other_edges
            sorted_edges = ClosureStrategy.sort_edges_by_chain(composite_edges)
            assert len(sorted_edges) == len(edges)
            for edge, next_edge in win_slice(sorted_edges, win_size=2, tail_cycling=True):
                assert edge.to_pid == next_edge.from_pid

    def test_sorted_edges_of_flower_cracks_with_self_intersection(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots

        edges = [
            Edge('7', '4', stretch=stretch),
            Edge('0', '4', stretch=stretch),
            Edge('4', '7', stretch=stretch),
            Edge('4', '6', stretch=stretch),
            Edge('6', '4', stretch=stretch),
            Edge('4', '5', stretch=stretch),
            Edge('5', '4', stretch=stretch),
        ]

        with pytest.raises(ValueError):
            ClosureStrategy.sort_edges_by_chain(edges)
