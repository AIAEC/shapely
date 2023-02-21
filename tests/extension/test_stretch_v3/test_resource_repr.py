class TestResourceRepr:
    def test_closure_repr(self, stretch_box):
        assert repr(stretch_box.closure('0')) == 'Closure([0,1,2,3,0])@0'

    def test_edge_seq_repr(self, stretch_box):
        assert repr(stretch_box.closure('0').exterior) == 'EdgeSeq(0,1,2,3,0)'

    def test_edge_repr(self, stretch_box):
        assert repr(stretch_box.edge('(0,1)')) == 'Edge(0,1)'

    def test_pivot_repr(self, stretch_box):
        assert repr(stretch_box.pivot('0')) == 'Pivot(0.00,0.00)@0'
