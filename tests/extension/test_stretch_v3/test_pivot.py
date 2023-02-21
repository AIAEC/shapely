from shapely.extension.model.stretch.stretch_v3 import Pivot


class TestPivotMethod:
    def test_pivot_attribute(self, stretch_box_with_exterior_crack):
        stretch = stretch_box_with_exterior_crack

        pivot = stretch.pivot('5')
        assert pivot.turning_back
        for i in range(5):
            assert not stretch.pivot(str(i)).turning_back

    def test_dangling_pivot_attribute(self, stretch_8_dangling_pivots):
        stretch = stretch_8_dangling_pivots

        for i in range(8):
            pivot = stretch.pivot(str(i))
            assert pivot.dangling
            assert not pivot.turning_back

    def test_connect_to_unclosed_seq(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

        edge_seq = Pivot.connect([stretch.pivot('0'), stretch.pivot('1'),
                                  stretch.pivot('2'), stretch.pivot('3')])
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 3
        assert len(stretch.closures) == 0
        assert edge_seq.closure is None
        assert len(edge_seq) == 3
        assert not edge_seq.closed

    def test_connect_to_closed_seq(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        edge_seq = Pivot.connect([stretch.pivot('0'), stretch.pivot('1'),
                                  stretch.pivot('2'), stretch.pivot('3'),
                                  stretch.pivot('0')])
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 0
        assert edge_seq.closure is None
        assert len(edge_seq) == 4
        assert edge_seq.closed

    def test_connect_same_pivot_multiple_time(self, stretch_4_dangling_pivots):
        stretch = stretch_4_dangling_pivots
        edge_seq = Pivot.connect([stretch.pivot('0'), stretch.pivot('0'), stretch.pivot('0')])
        assert len(edge_seq) == 0

        edge_seq = Pivot.connect([stretch.pivot('0'), stretch.pivot('0'), stretch.pivot('0'), stretch.pivot('1')])
        assert len(edge_seq) == 1
        assert edge_seq[0] is stretch.edge('(0,1)')
