class TestEdge:
    def test_reverse_negative_case(self, stretch_box):
        edge = stretch_box.edges[0]
        reverse = edge.reverse
        assert reverse is None

    def test_reverse_positive_case(self, stretch_2_boxes):
        edge = stretch_2_boxes.edges[1]
        assert edge.reverse is stretch_2_boxes.edges[7]
        assert stretch_2_boxes.edges[0].reverse is None
        assert stretch_2_boxes.edges[6].reverse is None

    def test_edge_attributes(self, stretch_box):
        edge = stretch_box.edges[0]
        assert len(edge) == 1
        assert edge[0] is edge
        assert edge[1] is edge
