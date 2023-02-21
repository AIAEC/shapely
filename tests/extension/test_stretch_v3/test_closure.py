from shapely.geometry import Polygon


class TestClosure:
    def test_search_seq_by_edge(self, stretch_box_holes):
        stretch = stretch_box_holes
        closure = stretch.closures[0]
        edge = stretch.edges[0]
        seq = closure.seq_of_edge(edge)
        assert seq is closure.exterior

        inner_edge = stretch.edges[4]
        seq = closure.seq_of_edge(inner_edge)
        assert seq is closure.interiors[0]

        inner_edge = stretch.edges[8]
        seq = closure.seq_of_edge(inner_edge)
        assert seq is closure.interiors[1]

        edge = (stretch.create_edge()
                .from_pivot(stretch.pivot('0'))
                .to_pivot(stretch.pivot('4'))
                .create())
        seq = closure.seq_of_edge(edge)
        assert seq is None

    def test_remove_crack(self, stretch_box_with_inner_crack):
        stretch = stretch_box_with_inner_crack

        assert len(stretch.closures) == 1
        assert len(stretch.edges) == 8
        assert len(stretch.pivots) == 7
        edge_seq = stretch.closures[0].interiors[0]
        assert len(edge_seq) == 4

        stretch.closures[0].remove_crack(gc=True)
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 0
        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]))
