from shapely.geometry import Polygon, box
from shapely.wkt import loads


class TestDifference:
    def test_difference_with_joint_poly(self, stretch_interior_offset_connected_in_in):
        stretch = stretch_interior_offset_connected_in_in

        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').interiors) == 2

        closure = stretch.closure('0')
        new_closures = closure.difference(box(50, 0, 60, 50))
        assert len(new_closures) == 1
        assert new_closures[0] is closure

        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').interiors) == 2

    def test_difference_with_corner(self, stretch_interior_offset_connected_in_in):
        stretch = stretch_interior_offset_connected_in_in
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').interiors) == 2

        closure = stretch.closure('0')
        new_closures = closure.difference(box(29, -1, 31, 1))
        assert len(new_closures) == 1
        assert closure.deleted
        assert new_closures[0] in stretch.closures
        assert closure not in stretch.closures
        assert len(stretch.pivots) == 16
        assert len(stretch.edges) == 16
        assert len(stretch.closures) == 1
        assert len(stretch.closures[0].interiors) == 2
        assert stretch.closures[0].shape.equals(loads('POLYGON ((0 0, 29 0, 29 1, 30 1, 30 30, 0 30, 0 0), (5 25, 25 25, 25 20, 20 20, 10 20, 5 20, 5 25), (8 12, 22 12, 22 8, 8 8, 8 12))'))

    def test_difference_and_cut_into_2_pieces(self, stretch_interior_offset_connected_in_in):
        stretch = stretch_interior_offset_connected_in_in
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 14
        assert len(stretch.closures) == 1
        assert len(stretch.closure('0').interiors) == 2

        closure = stretch.closure('0')
        new_closures = closure.difference(box(15, -1, 16, 31))
        assert len(new_closures) == 2
        assert closure.deleted
        assert new_closures[0] in stretch.closures
        assert new_closures[1] in stretch.closures
        assert closure not in stretch.closures
        assert len(stretch.pivots) == 26
        assert len(stretch.edges) == 26
        assert len(stretch.closures) == 2
        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.x)
        assert len(closures[0].interiors) == 0
        assert len(closures[1].interiors) == 0
        assert closures[0].shape.equals(loads('POLYGON ((0 0, 15 0, 15 8, 8 8, 8 12, 15 12, 15 20, 10 20, 5 20, 5 25, 15 25, 15 30, 0 30, 0 0))'))
        assert closures[1].shape.equals(loads('POLYGON ((30 30, 16 30, 16 25, 25 25, 25 20, 20 20, 16 20, 16 12, 22 12, 22 8, 16 8, 16 0, 30 0, 30 30))'))




