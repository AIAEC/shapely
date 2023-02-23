import pytest

from shapely.extension.model.stretch.offset import Offset
from shapely.extension.model.stretch.offset_strategy import NaiveAttachOffsetHandler, StrictAttachOffsetHandler
from shapely.extension.model.stretch.stretch_v3 import EdgeSeq
from shapely.geometry import LineString, Polygon
from shapely.wkt import loads


class TestOffset:
    def test_offset_exterior_edge_inner_hit_hit_default_handler(
            self, stretch_exterior_offset_hit_hit_no_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_no_reverse_closure
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 6

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1

        edge_seq = edge_seqs[0]
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, 10), (20, 10)]))

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 10, 20 10, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_exterior_edge_inner_hit_hit_default_handler_with_reverse_closure(
            self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1

        edge_seq = edge_seqs[0]
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, 10), (20, 10)]))

        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 16

        assert stretch.closure('0') is None, 'origin closure should be removed'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert len(closures[0].interiors) == 0
        assert closures[0].shape.equals(loads('POLYGON ((0 0, 0 -10, 30 -10, 30 0, 20 0, 20 10, 10 10, 10 0, 0 0))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(loads('POLYGON ((0 0, 10 0, 10 10, 20 10, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_exterior_edge_seq_inner_hit_hit_default_handler_with_reverse_closure(
            self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12

        edge_seq = stretch.edge_seq(['0', '1', '2', '3'])
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 3

        edge_seqs = Offset(edge_seq, NaiveAttachOffsetHandler).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1

        edge_seq = edge_seqs[0]
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(0, 10), (30, 10)]))
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 10

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert len(closures[0].interiors) == 0
        assert closures[0].shape.equals(loads('POLYGON ((0 0, 0 -10, 30 -10, 30 0, 30 10, 0 10, 0 0))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(loads('POLYGON ((30 20, 0 20, 0 10, 30 10, 30 20))'))

    def test_offset_exterior_edge_inner_hit_in_default_handler(
            self, stretch_exterior_offset_hit_in_no_reverse_closure):
        stretch = stretch_exterior_offset_hit_in_no_reverse_closure
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1

        edge_seq = edge_seqs[0]
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, 10), (18, 10)]))
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 10, 18 10, 18 12, 22 12, 22 8, 20 8, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_exterior_edge_inner_hit_in_default_handler_with_reverse_closure(
            self, stretch_exterior_offset_hit_in_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_in_with_reverse_closure
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 16

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1

        edge_seq = edge_seqs[0]
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, 10), (18, 10)]))
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 15
        assert len(stretch.edges) == 22

        assert stretch.closure('0') is None, 'origin closure should be removed'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert len(closures[0].interiors) == 0
        assert closures[0].shape.equals(
            loads('POLYGON ((0 0, 0 -10, 30 -10, 30 0, 20 0, 20 8, 18 8, 18 10, 10 10, 10 0, 0 0))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 10, 18 10, 18 12, 22 12, 22 8, 20 8, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_exterior_edge_inner_hit_out_default_handler(
            self, stretch_exterior_offset_hit_out_no_reverse_closure):
        stretch = stretch_exterior_offset_hit_out_no_reverse_closure
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, 10), (15, 10)]))
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10
        assert stretch.closure('0') is None, 'origin closure should be removed'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.x)
        assert len(closures[0].interiors) == 0
        assert closures[0].shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (15, 10), (15, 20), (0, 20), (0, 0)]))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(Polygon([(20, 5), (20, 0), (30, 0), (30, 5)]))

    def test_offset_exterior_edge_inner_hit_out_default_handler_with_reverse_closure(
            self, stretch_exterior_offset_hit_out_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_out_with_reverse_closure
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 14

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, 10), (15, 10)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.closures) == 3
        assert len(stretch.pivots) == 13
        assert len(stretch.edges) == 20

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert len(closures[0].interiors) == 0
        assert closures[0].shape.equals(
            loads('POLYGON ((0 0, 0 -10, 30 -10, 30 0, 20 0, 20 5, 15 5, 15 10, 10 10, 10 0, 0 0))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(
            loads('POLYGON ((20 5, 20 0, 30 0, 30 5, 20 5))'))

        assert len(closures[2].interiors) == 0
        assert closures[2].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 10, 15 10, 15 20, 0 20, 0 0))'))

    def test_offset_exterior_edge_inner_in_in_default_handler(
            self, stretch_exterior_offset_in_in_no_reverse_closure):
        stretch = stretch_exterior_offset_in_in_no_reverse_closure
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(12, 10), (18, 10)]))
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16

        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 10 0, 10 8, 8 8, 8 12, 12 12, 12 10, 18 10, 18 12, 22 12, 22 8, 20 8, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_exterior_edge_inner_connected_in_in_default_handler(
            self, stretch_exterior_offset_connected_in_in_no_reverse_closure):
        stretch = stretch_exterior_offset_connected_in_in_no_reverse_closure
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert len(edge_seqs) == 0

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 2, 8 2, 8 18, 22 18, 22 2, 20 2, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_exterior_edge_inner_in_out_default_handler(
            self, stretch_exterior_offset_in_out_no_reverse_closure):
        stretch = stretch_exterior_offset_in_out_no_reverse_closure
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(12, 10), (15, 10)]))
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert stretch.closure('0') is None, 'origin closure should be removed'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.x)
        assert len(closures[0].interiors) == 0
        assert closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 8, 8 8, 8 12, 12 12, 12 10, 15 10, 15 20, 0 20, 0 0))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(loads('POLYGON ((20 8, 20 0, 30 0, 30 8, 20 8))'))

    def test_offset_exterior_edge_inner_out_out_default_handler(self,
                                                                stretch_exterior_offset_hit_hit_no_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_no_reverse_closure
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 6

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(30)
        assert len(edge_seqs) == 0

        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert stretch.closure('0') is None, 'origin closure should be removed'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.x)
        assert len(closures[0].interiors) == 0
        assert closures[0].shape.equals(Polygon([(0, 0), (10, 0), (10, 20), (0, 20)]))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(Polygon([(20, 0), (30, 0), (30, 20), (20, 20)]))

    def test_offset_exterior_edge_interrupted_hit_hit_default_handler(
            self, stretch_exterior_offset_interrupted_hit_hit_no_reverse_closure):
        stretch = stretch_exterior_offset_interrupted_hit_hit_no_reverse_closure

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 2
        edge_seqs.sort(key=lambda edge_seq: edge_seq.shape.centroid.x)

        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, 10), (13, 10)]))

        edge_seq = edge_seqs[1]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(17, 10), (20, 10)]))

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 10, 13 10, 13 18, 17 18, 17 10, 20 10, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_interior_edge_hit_hit_default_handler(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(20, 10), (10, 10)]))

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (20 10, 10 10, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 10))'))

    def test_offset_interior_edge_interrupted_hit_hit_default_handler(
            self, stretch_interior_offset_interrupted_hit_hit):
        stretch = stretch_interior_offset_interrupted_hit_hit
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closure('0').interiors) == 2

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 2
        edge_seqs.sort(key=lambda edge_seq: edge_seq.shape.centroid.x)

        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(13, 10), (10, 10)]))

        edge_seq = edge_seqs[1]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(20, 10), (17, 10)]))

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16
        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (17 8, 13 8, 13 10, 10 10, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 10, 17 10, 17 8))'))

    def test_offset_interior_edge_hit_hit_contained_hole_default_handler(
            self, stretch_interior_offset_interrupted_hit_hit):
        stretch = stretch_interior_offset_interrupted_hit_hit
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closure('0').interiors) == 2

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(18)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(20, 2), (10, 2)]))

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (20 2, 10 2, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 2))'))

    def test_offset_interior_edge_hit_in_default_handler(
            self, stretch_interior_offset_hit_in):
        stretch = stretch_interior_offset_hit_in

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(5)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1

        assert edge_seq.shape.equals(LineString([(18, 15), (10, 15)]))
        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (22 18, 22 12, 18 12, 18 15, 10 15, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 18, 22 18))'))

    def test_offset_interior_edge_hit_out_default_handler(
            self, stretch_interior_offset_hit_out):
        stretch = stretch_interior_offset_hit_out

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        edge = stretch.edge('(9,10)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]

        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(15, 10), (10, 10)]))
        assert len(stretch.closures) == 1
        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 15 0, 15 10, 10 10, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 15, 30 15, 30 30, 0 30, 0 0))'))

    def test_offset_interior_edge_in_in_default_handler(self, stretch_interior_offset_in_in):
        stretch = stretch_interior_offset_in_in

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 3
        assert len(stretch.pivots) == 18
        assert len(stretch.edges) == 18

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(12, 10), (18, 10)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 20
        assert len(stretch.edges) == 20
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (8 12, 10 12, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 12, 22 12, 22 8, 18 8, 18 10, 12 10, 12 8, 8 8, 8 12))'))

    def test_offset_interior_edge_in_in_connected_default_handler(self, stretch_interior_offset_connected_in_in):
        stretch = stretch_interior_offset_connected_in_in

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert len(edge_seqs) == 0

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (8 12, 10 12, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 12, 22 12, 22 8, 8 8, 8 12))'))

    def test_offset_interior_edge_in_out_default_handler(self, stretch_interior_offset_connected_in_out):
        stretch = stretch_interior_offset_connected_in_out

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16

        edge = stretch.edge('(9,10)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(10)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1

        assert edge_seq.shape.equals(LineString([(12, 10), (15, 10)]))
        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 18
        assert len(stretch.edges) == 18
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 15 0, 15 10, 12 10, 12 8, 8 8, 8 12, 10 12, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 15, 30 15, 30 30, 0 30, 0 0))'))

    def test_offset_interior_out_out_default_handler(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(30)
        assert len(edge_seqs) == 0

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 0, 30 0, 30 30, 0 30, 0 0))'))

    def test_offset_exterior_outer(self, stretch_exterior_offset_hit_hit_no_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_no_reverse_closure

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 6

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(-5)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, -5), (20, -5)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 -5, 20 -5, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_exterior_outer_with_reverse_closure(self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure

        assert len(stretch.closures) == 2
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.closures[1].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(-5)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(10, -5), (20, -5)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 16
        assert len(stretch.closures) == 2
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.closures[1].interiors) == 0
        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.y)

        assert closures[0].shape.equals(loads('POLYGON ((0 0, 0 -10, 30 -10, 30 0, 20 0, 20 -5, 10 -5, 10 0, 0 0))'))
        assert closures[1].shape.equals(loads('POLYGON ((0 0, 10 0, 10 -5, 20 -5, 20 0, 30 0, 30 20, 0 20, 0 0))'))

    def test_offset_interior_outer_into_hole_default_handler(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(-2)
        assert all(isinstance(edge_seq, EdgeSeq) for edge_seq in edge_seqs)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(20, 22), (10, 22)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (10 22, 10 20, 5 20, 5 25, 25 25, 25 20, 20 20, 20 22, 10 22))'))

    def test_offset_interior_outer_into_inner_space_default_handler(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(-6)
        assert len(edge_seqs) == 0
        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (10 25, 10 20, 5 20, 5 25, 10 25), (20 25, 25 25, 25 20, 20 20, 20 25))'))

    def test_offset_interior_outer_into_outer_space_default_handler(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(7,8)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(-15)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(20, 35), (10, 35)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 20 30, 20 35, 10 35, 10 30, 0 30, 0 0), (20 25, 25 25, 25 20, 20 20, 20 25), (10 25, 10 20, 5 20, 5 25, 10 25))'))

    def test_offset_interior_outer_into_hole_hit_in_default_handler(self, stretch_interior_offset_into_hole_in_hit):
        stretch = stretch_interior_offset_into_hole_in_hit

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        edge = stretch.edge('(9,10)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(-13)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(15, 23), (10, 23)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (20 20, 25 20, 25 10, 20 10, 20 20), (10 10, 5 10, 5 25, 15 25, 15 23, 10 23, 10 10))'))

    def test_offset_interior_outer_into_hole_hit_hit_interrupted_default_handler(
            self, stretch_interior_offset_into_hole_hit_hit_interrupted):
        stretch = stretch_interior_offset_into_hole_hit_hit_interrupted

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14

        edge = stretch.edge('(11,12)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge).offset(-13)
        edge_seqs.sort(key=lambda edge_seq: edge_seq.shape.centroid.x)
        assert len(edge_seqs) == 2
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(12, 23), (10, 23)]))

        edge_seq = edge_seqs[1]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(20, 23), (18, 23)]))

        assert stretch.closure('0') is None, 'origin closure should be removed'

        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (25 10, 20 10, 20 23, 18 23, 18 25, 25 25, 25 10), (10 10, 5 10, 5 25, 12 25, 12 23, 10 23, 10 10))'))

    def test_offset_exterior_edge_inner_hit_in_naive_attach_handler_with_reverse_closure(
            self, stretch_exterior_offset_hit_in_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_in_with_reverse_closure
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 16

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, NaiveAttachOffsetHandler).offset(10)

        assert len(edge_seqs) == 2
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(0, 10), (18, 10)]))

        edge_seq = edge_seqs[1]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(22, 10), (30, 10)]))

        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 18

        assert stretch.closure('0') is None, 'origin closure should be removed'
        assert stretch.closure('1') is None, 'origin closure should be removed'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert len(closures[0].interiors) == 0
        assert len(closures[1].interiors) == 0

        assert closures[0].shape.equals(
            loads('POLYGON ((0 0, 0 -10, 30 -10, 30 0, 30 10, 22 10, 22 8, 18 8, 18 10, 0 10, 0 0))'))
        assert closures[1].shape.equals(loads('POLYGON ((0 10, 18 10, 18 12, 22 12, 22 10, 30 10, 30 20, 0 20, 0 10))'))

    def test_offset_exterior_edge_outside_of_closure_naive_handler(
            self, stretch_exterior_offset_hit_in_no_reverse_closure):
        stretch = stretch_exterior_offset_hit_in_no_reverse_closure

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10

        edge = stretch.edge('(1,2)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, NaiveAttachOffsetHandler).offset(30)
        assert len(edge_seqs) == 0

        assert len(stretch.closures) == 0
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0

    def test_offset_exterior_edge_inner_hit_hit_with_strict_attach_handler(
            self, stretch_0_for_strict_attach_offset_handler):
        stretch = stretch_0_for_strict_attach_offset_handler
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        edge = stretch.edge('(4,5)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(15)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1

        assert edge_seq.shape.equals(LineString([(20, 5), (10, 5)]))
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 30 0, 30 10, 20 10, 20 5, 10 5, 10 10, 0 10, 0 0))'))

    def test_offset_exterior_edge_inner_attaching_to_adjacent_edge_with_strict_attach_handler(
            self, stretch_1_for_strict_attach_offset_handler):
        stretch = stretch_1_for_strict_attach_offset_handler

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        edge = stretch.edge('(4,5)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(5)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(11.5, 15), (18.5, 15)]))

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 30 0, 30 10, 17 10, 18.5 15, 11.5 15, 13 10, 0 10, 0 0))'))

    def test_offset_exterior_edge_inner_switching_to_perpendicular_attachment_with_strict_attach_handler(
            self, stretch_1_for_strict_attach_offset_handler):
        stretch = stretch_1_for_strict_attach_offset_handler

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        edge = stretch.edge('(4,5)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(15)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(13, 5), (17, 5)]))

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 30 0, 30 10, 17 10, 17 5, 13 5, 13 10, 0 10, 0 0))'))

    def test_offset_exterior_edge_inner_extrude_with_strict_attach_handler(
            self, stretch_1_for_strict_attach_offset_handler):
        stretch = stretch_1_for_strict_attach_offset_handler

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        edge = stretch.edge('(4,5)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(30)
        assert len(edge_seqs) == 0

        assert len(stretch.closures) == 0
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0

    def test_offset_exterior_edge_outer_with_perpendicular_attachment_with_strict_attach_handler(
            self, stretch_1_for_strict_attach_offset_handler):
        stretch = stretch_1_for_strict_attach_offset_handler

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8

        edge = stretch.edge('(4,5)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(-5)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(20, 25), (10, 25)]))

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10
        assert stretch.closures[0].shape.equals(
            loads('POLYGON ((0 0, 30 0, 30 10, 17 10, 20 20, 20 25, 10 25, 10 20, 13 10, 0 10, 0 0))'))

    def test_offset_interior_edge_inner_attaching_to_adjacent_edge_with_strict_offset_handler(
            self, stretch_2_for_strict_attach_offset_handler):
        stretch = stretch_2_for_strict_attach_offset_handler

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        edge = stretch.edge('(6,7)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(2)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(11.2, 22), (18.8, 22)]))

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (25 10, 5 10, 5 25, 13 25, 11.2 22, 18.8 22, 17 25, 25 25, 25 10))'))

    def test_offset_interior_edge_inner_switching_to_perpendicular_attachment_with_strict_offset_handler(
            self, stretch_2_for_strict_attach_offset_handler):
        stretch = stretch_2_for_strict_attach_offset_handler

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        edge = stretch.edge('(6,7)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(7)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(13, 27), (17, 27)]))

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12
        assert stretch.closures[0].shape.equals(
            loads(
                'POLYGON ((0 0, 30 0, 30 30, 0 30, 0 0), (25 10, 5 10, 5 25, 13 25, 13 27, 17 27, 17 25, 25 25, 25 10))'))

    def test_offset_interior_edge_inner_extrude_with_strict_offset_handler(
            self, stretch_2_for_strict_attach_offset_handler):
        stretch = stretch_2_for_strict_attach_offset_handler

        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 1
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 12

        edge = stretch.edge('(6,7)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(15)
        assert len(edge_seqs) == 0

        assert len(stretch.closures) == 0
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0

    def test_offset_inner_box_exterior_edge_towards_outer_space(self, stretch_outer_and_inner_closures):
        stretch = stretch_outer_and_inner_closures

        assert len(stretch.closures) == 2
        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures[0].interiors) == 1
        assert len(closures[1].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12

        edge = stretch.edge('(4,5)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(-0.1)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1

        assert edge_seq.shape.equals(LineString([(0.5, 0.4), (0.6, 0.4)]))
        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures) == 2
        assert len(closures[0].interiors) == 1
        assert closures[0].shape.equals(loads(
            'POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0), (0.5 0.5, 0.5 0.6, 0.6 0.6, 0.6 0.5, 0.6 0.4, 0.5 0.4, 0.5 0.5))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(
            loads('POLYGON ((0.5 0.5, 0.5 0.4, 0.6 0.4, 0.6 0.5, 0.6 0.6, 0.5 0.6, 0.5 0.5))'))

    def test_offset_inner_box_exterior_edge_towards_inner_space(self, stretch_outer_and_inner_closures):
        stretch = stretch_outer_and_inner_closures

        assert len(stretch.closures) == 2
        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures[0].interiors) == 1
        assert len(closures[1].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12

        edge = stretch.edge('(4,5)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(0.05)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1

        assert edge_seq.shape.equals(LineString([(0.5, 0.55), (0.6, 0.55)]))
        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures) == 2
        assert len(closures[0].interiors) == 1
        assert closures[0].shape.equals(
            loads('POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0), (0.6 0.6, 0.6 0.55, 0.5 0.55, 0.5 0.6, 0.6 0.6))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(
            loads('POLYGON ((0.6 0.6, 0.5 0.6, 0.5 0.55, 0.6 0.55, 0.6 0.6))'))

    def test_offset_outer_box_interior_edge_towards_outer_space(self, stretch_outer_and_inner_closures):
        stretch = stretch_outer_and_inner_closures

        assert len(stretch.closures) == 2
        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures[0].interiors) == 1
        assert len(closures[1].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12

        edge = stretch.edge('(5,4)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(-0.05)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(0.6, 0.55), (0.5, 0.55)]))

        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures) == 2
        assert len(closures[0].interiors) == 1
        assert closures[0].shape.equals(
            loads('POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0), (0.6 0.6, 0.6 0.55, 0.5 0.55, 0.5 0.6, 0.6 0.6))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(
            loads('POLYGON ((0.6 0.6, 0.5 0.6, 0.5 0.55, 0.6 0.55, 0.6 0.6))'))

    def test_offset_outer_box_interior_edge_towards_inner_space(self, stretch_outer_and_inner_closures):
        stretch = stretch_outer_and_inner_closures

        assert len(stretch.closures) == 2
        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures[0].interiors) == 1
        assert len(closures[1].interiors) == 0
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12

        edge = stretch.edge('(5,4)')
        assert edge in stretch.edges

        edge_seqs = Offset(edge, StrictAttachOffsetHandler).offset(0.1)
        assert len(edge_seqs) == 1
        edge_seq = edge_seqs[0]
        assert isinstance(edge_seq, EdgeSeq)
        assert len(edge_seq) == 1
        assert edge_seq.shape.equals(LineString([(0.6, 0.4), (0.5, 0.4)]))

        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert len(closures) == 2
        assert len(closures[0].interiors) == 1
        assert closures[0].shape.equals(loads(
            'POLYGON ((0 0, 1 0, 1 1, 0 1, 0 0), (0.5 0.5, 0.5 0.6, 0.6 0.6, 0.6 0.5, 0.6 0.4, 0.5 0.4, 0.5 0.5))'))

        assert len(closures[1].interiors) == 0
        assert closures[1].shape.equals(
            loads('POLYGON ((0.5 0.5, 0.5 0.4, 0.6 0.4, 0.6 0.5, 0.6 0.6, 0.5 0.6, 0.5 0.5))'))

    def test_offset_exterior_inner_and_union_space_to_multiple_reverse_closures(
            self, stretch_offset_union_2_reverse_closure):
        stretch = stretch_offset_union_2_reverse_closure
        assert len(stretch.closures) == 3
        assert len(stretch.edges) == 14
        assert len(stretch.pivots) == 10

        edge_seq = EdgeSeq([stretch.edge('(2,3)'),
                            stretch.edge('(3,4)'),
                            stretch.edge('(4,5)')])
        with pytest.raises(AssertionError):
            Offset(edge_seq, StrictAttachOffsetHandler).offset(1)

    def test_offset_exterior_edges_one_by_one_to_inner_space(
            self, stretch_offset_union_2_reverse_closure):
        stretch = stretch_offset_union_2_reverse_closure
        assert len(stretch.closures) == 3
        assert len(stretch.edges) == 14
        assert len(stretch.pivots) == 10

        edge_seq = EdgeSeq([stretch.edge('(2,3)'),
                            stretch.edge('(3,4)'),
                            stretch.edge('(4,5)')])
        for edge in edge_seq:
            Offset(edge, StrictAttachOffsetHandler).offset(1)

        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 18
        assert len(stretch.closures) == 3

        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert all(len(closure.interiors) == 0 for closure in closures)

        assert closures[0].shape.equals(loads('POLYGON ((4 6, 4 7, 4 12, 0 12, 0 7, 0 6, 4 6))'))
        assert closures[1].shape.equals(loads('POLYGON ((0 0, 12 0, 12 6, 8 6, 4 6, 0 6, 0 0))'))
        assert closures[2].shape.equals(loads('POLYGON ((12 6, 12 7, 12 12, 8 12, 8 7, 8 6, 12 6))'))

    @pytest.mark.skip(reason='to fix?')
    def test_offset_twice(self,
                          stretch_of_three_closures):
        """
    ┌─────────────────────┐
    │                     │
    │                     │
    │                     │
    │                     │
    │      ▲          ▲   │
    │      │          │   │
    ├──────────────┬──────┤
    │              │      │
    │              │      │
    └──────────────┴──────┘
        """
        stretch = stretch_of_three_closures
        assert len(stretch.closures) == 3
        assert len(stretch.edges) == 13
        assert len(stretch.pivots) == 8

        edge_seq = EdgeSeq([stretch.edge('(3,4)'),
                            stretch.edge('(4,5)')])
        for edge in edge_seq:
            Offset(edge, StrictAttachOffsetHandler).offset(150)

        assert all([closure.shape.area in [40 * 100, 160 * 75, 160 * 25] for closure in stretch.closures])
