import pytest

from shapely.geometry import Polygon, box, Point, LineString, MultiPoint
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

        expect_closure_shape = loads('POLYGON ((0 0, 29 0, 29 1, 30 1, 30 30, 0 30, 0 0), (5 25, 25 25, 25 20, 20 20, 10 20, 5 20, 5 25), (8 12, 22 12, 22 8, 8 8, 8 12))')
        # difference has precision problem, thus only assert the area almost equal
        assert stretch.closures[0].shape.area == pytest.approx(expect_closure_shape.area)

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

        # difference has precision problem, thus only assert the area almost equal
        closure0_expect_shape = loads('POLYGON ((0 0, 15 0, 15 8, 8 8, 8 12, 15 12, 15 20, 10 20, 5 20, 5 25, 15 25, 15 30, 0 30, 0 0))')
        assert closures[0].shape.area == pytest.approx(closure0_expect_shape.area)

        closure1_expect_shape = loads('POLYGON ((30 30, 16 30, 16 25, 25 25, 25 20, 20 20, 16 20, 16 12, 22 12, 22 8, 16 8, 16 0, 30 0, 30 30))')
        assert closures[1].shape.area == pytest.approx(closure1_expect_shape.area)

    def test_difference_to_keep_cargo_inherited(self, stretch_box):
        stretch = stretch_box
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        closure = stretch.closures[0]
        closure.cargo['test'] = 'closure'
        pivot = stretch.pivots_by_query(Point(0, 0))[0]
        pivot.cargo['test'] = 'pivot'
        edge = stretch.edges_by_query(Point(0.5, 0))[0]
        edge.cargo['test'] = 'edge'

        new_closures = closure.difference(box(0.4, -1, 0.5, 2))
        assert len(new_closures) == 2
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 2

        for new_closure in new_closures:
            assert new_closure.cargo.get('test') == 'closure'

        new_pivot = stretch.pivots_by_query(Point(0, 0))[0]
        assert new_pivot.cargo.get('test') == 'pivot'

        new_edges = stretch.edges_by_query(MultiPoint([Point(0.2, 0), Point(0.8, 0)]))
        for new_edge in new_edges:
            assert new_edge.cargo.get('test') == 'edge'

