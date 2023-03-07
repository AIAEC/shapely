from shapely.extension.model.stretch.creator import ClosureReconstructor
from shapely.extension.model.stretch.stretch_v3 import Stretch
from shapely.geometry import Polygon


class TestClosureReconstruction:
    def test_reconstruct_by_nothing(self):
        stretch = Stretch()
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

        closures = ClosureReconstructor(stretch).reconstruct()
        assert not closures
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

    def test_reconstruct_closure_without_hole(self, stretch_4_dangling_edge):
        stretch = stretch_4_dangling_edge
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 0

        closures = ClosureReconstructor(stretch).from_edges(stretch.edges).reconstruct()
        assert len(closures) == 1
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert stretch.closure('0').shape.equals(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))

    def test_reconstruct_closure_with_holes_0(self, stretch_8_dangling_edges):
        stretch = stretch_8_dangling_edges

        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 0

        closures = ClosureReconstructor(stretch).from_edges(stretch.edges).reconstruct()
        assert len(closures) == 1
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 1
        assert stretch.closure('0').shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                                                         [[(1, 1), (2, 1), (2, 2), (1, 2)]]))

    def test_reconstruct_closures_given_redundant_reverse_edge(self, stretch_2_groups_dangling_edges):
        stretch = stretch_2_groups_dangling_edges

        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 0

        closures = ClosureReconstructor(stretch).from_edges(stretch.edges[:6]).reconstruct()
        assert len(closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 1
        assert stretch.closure('0').shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]))