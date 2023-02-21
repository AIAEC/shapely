class TestDeletion:
    def test_discard_edge_without_gc(self, stretch_box):
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 4
        assert len(stretch_box.closures) == 1

        stretch_box.discard_edge('(0,1)')
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 3
        assert len(stretch_box.closures) == 1, 'closure should not be deleted by low level api'

    def test_discard_edge_with_gc(self, stretch_box):
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 4
        assert len(stretch_box.closures) == 1

        stretch_box.discard_edge('(0,1)', gc=True)
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 3
        assert len(stretch_box.closures) == 1, 'closure should not be deleted by low level api'

        stretch_box.discard_edge('(3,0)', gc=True)
        assert len(stretch_box.pivots) == 3
        assert len(stretch_box.edges) == 2
        assert len(stretch_box.closures) == 1, 'closure should be not deleted by low level api'

    def test_delete_closure_without_gc(self, stretch_box):
        stretch_box.delete_closure('0')
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 4
        assert len(stretch_box.closures) == 0
        assert all(len(pivot.in_edges) == 1 for pivot in stretch_box.pivots)
        assert all(len(pivot.out_edges) == 1 for pivot in stretch_box.pivots)

    def test_delete_closure_with_gc(self, stretch_box):
        stretch_box.delete_closure('0', gc=True)
        assert len(stretch_box.pivots) == 0
        assert len(stretch_box.edges) == 0
        assert len(stretch_box.closures) == 0

    def test_delete_edge_without_gc(self, stretch_box):
        stretch_box.delete_edge(stretch_box.edges[0])
        assert len(stretch_box.pivots) == 4
        assert len(stretch_box.edges) == 3
        assert len(stretch_box.closures) == 0
        assert not stretch_box.pivot('0').out_edges
        assert not stretch_box.pivot('1').in_edges

    def test_delete_edge_with_gc(self, stretch_box):
        stretch_box.delete_edge(stretch_box.edges[0], gc=True)
        assert len(stretch_box.pivots) == 0
        assert len(stretch_box.edges) == 0
        assert len(stretch_box.closures) == 0

    def test_delete_interior_edge_without_gc(self, stretch_box_holes):
        stretch_box_holes.delete_edge(stretch_box_holes.edges[4])
        assert len(stretch_box_holes.pivots) == 12
        assert len(stretch_box_holes.edges) == 11
        assert len(stretch_box_holes.closures) == 1
        assert not stretch_box_holes.pivot('7').out_edges
        assert not stretch_box_holes.pivot('6').in_edges
        assert len(stretch_box_holes.closures[0].interiors) == 1

    def test_delete_interior_edge_with_gc(self, stretch_box_holes):
        stretch_box_holes.delete_edge(stretch_box_holes.edges[4], gc=True)
        assert len(stretch_box_holes.pivots) == 8
        assert len(stretch_box_holes.edges) == 8
        assert len(stretch_box_holes.closures) == 1
        assert len(stretch_box_holes.closures[0].interiors) == 1

    def test_delete_pivot_without_gc(self, stretch_box):
        stretch_box.delete_pivot(stretch_box.pivots[0])
        assert len(stretch_box.pivots) == 3
        assert len(stretch_box.edges) == 2
        assert len(stretch_box.closures) == 0
        assert not stretch_box.pivot('0')

    def test_delete_pivot_with_gc(self, stretch_box):
        stretch_box.delete_pivot(stretch_box.pivots[0], gc=True)
        assert len(stretch_box.pivots) == 0
        assert len(stretch_box.edges) == 0
        assert len(stretch_box.closures) == 0
