from copy import deepcopy

import pytest

from shapely.extension.model.stretch.stretch_v3 import Edge, EdgeSeq
from shapely.geometry import Polygon


class TestEdgeSequence:
    def test_edge_seq_attribute(self, stretch_box):
        edge_seq = stretch_box.closures[0].exterior
        assert len(edge_seq) == 4
        assert edge_seq.from_pid == edge_seq[0].from_pid
        assert edge_seq.to_pid == edge_seq[-1].to_pid

        assert isinstance(edge_seq[:2], EdgeSeq)
        assert isinstance(edge_seq[0], Edge)

    def test_edge_seq_remove_crack_on_exterior(self, stretch_box_with_exterior_crack):
        stretch = stretch_box_with_exterior_crack

        assert len(stretch.closures) == 1
        assert len(stretch.edges) == 7
        assert len(stretch.pivots) == 6
        edge_seq = stretch.closures[0].exterior
        assert len(edge_seq) == 7
        assert edge_seq.closed

        edge_seq.remove_crack(gc=True)
        assert len(edge_seq) == 5
        assert edge_seq.closed
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert len(stretch.closures) == 1
        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (5, 0), (10, 0), (10, 10), (0, 10)]))

    def test_edge_seq_remove_crack_on_interior(self, stretch_box_with_inner_crack):
        stretch = stretch_box_with_inner_crack

        assert len(stretch.closures) == 1
        assert len(stretch.edges) == 8
        assert len(stretch.pivots) == 7
        edge_seq = stretch.closures[0].interiors[0]
        assert len(edge_seq) == 4

        edge_seq.remove_crack(gc=False)
        assert len(edge_seq) == 0

        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1  # because we don't call remove crack on closure
        assert len(stretch.closures[0].interiors[0]) == 0

        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]))

    def test_replace_with_origin_edge(self, stretch_box):
        stretch = stretch_box
        edge_seq = stretch.closures[0].exterior
        assert len(edge_seq) == 4

        edge_seq_copy = deepcopy(edge_seq)
        edge_seq_copy.replace_and_discard(stretch.edges[0], stretch.edges[0])
        assert len(edge_seq_copy) == 4
        for origin_edge, edge in zip(edge_seq, edge_seq_copy):
            assert origin_edge == edge

    def test_replace_with_origin_edge_seq(self, stretch_box):
        stretch = stretch_box
        edge_seq = stretch.closures[0].exterior
        assert len(edge_seq) == 4

        edge_seq_copy = deepcopy(edge_seq)
        edge_seq_copy.replace_and_discard(edge_seq_copy[:2], edge_seq_copy[:2])
        assert len(edge_seq_copy) == 4
        for origin_edge, edge in zip(edge_seq, edge_seq_copy):
            assert origin_edge == edge

    def test_replace_with_edge_not_in_sequence(self, stretch_box):
        stretch = stretch_box
        edge_seq = stretch.closures[0].exterior
        assert len(edge_seq) == 4

        edge_seq_copy = deepcopy(edge_seq)
        with pytest.raises(ValueError):
            edge_seq.replace_and_discard(stretch.edges[0], Edge('1', '0', stretch))

        for origin_edge, edge in zip(edge_seq, edge_seq_copy):
            assert origin_edge == edge
