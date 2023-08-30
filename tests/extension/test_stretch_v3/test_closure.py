from shapely.geometry import Polygon
from shapely.wkt import loads


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

    def test_shape(self, stretch_box_duplicate_pivots, stretch_box_holes, stretch_box_with_exterior_crack):
        shape = stretch_box_duplicate_pivots.closures[0].shape
        assert shape.is_valid
        assert shape.equals(loads("POLYGON ((0 0, 0.3 0, 1 0, 1 1, 0 1, 0 0))"))

        shape = stretch_box_holes.closures[0].shape
        assert shape.is_valid
        assert shape.interiors.__len__() == 2
        assert shape.area == 10 * 10 - 1 * 1 * 2
        assert shape.equals(
            loads("POLYGON ((0 0, 10 0, 10 10, 0 10, 0 0), (2 2, 2 3, 3 3, 3 2, 2 2), (9 6, 9 5, 8 5, 8 6, 9 6))"))

        shape = stretch_box_with_exterior_crack.closures[0].shape
        assert shape.is_valid
        assert shape.equals(loads("POLYGON ((0 0, 5 0, 5 5, 5 0, 10 0, 10 10, 0 10, 0 0))"))

    def test_invalid_shape(self, stretch_closure_resembling_line):
        assert stretch_closure_resembling_line.closures[0].real_shape.equals(loads("POLYGON ((0 0, 1 0, 2 0, 0 0))"))
