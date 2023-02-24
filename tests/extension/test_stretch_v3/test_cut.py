from shapely.extension.constant import MATH_MIDDLE_EPS

from shapely.extension.model.stretch.cut import Cut
from shapely.geometry import LineString, Polygon, LinearRing, Point
from shapely.wkt import loads


class TestCut:
    def test_cut_box_1_time(self, stretch_box):
        stretch = stretch_box
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(0.1, -1), (0.1, 2)]))
                    .closures())
        assert len(closures) == 2
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert stretch.closure('0') is None, 'closure 0 should be removed'

        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert closures[0].shape.equals(Polygon([(0, 0), (0.1, 0), (0.1, 1), (0, 1)]))
        assert closures[1].shape.equals(Polygon([(0.1, 0), (1, 0), (1, 1), (0.1, 1)]))

    def test_cut_box_multiple_times(self, stretch_box):
        stretch = stretch_box
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(0.1, -1), (0.1, 2)]))
                    .by(LineString([(0.2, -1), (0.2, 2)]))
                    .by(LineString([(0.3, -1), (0.3, 2)]))
                    .closures())
        assert len(closures) == 4
        assert len(stretch.closures) == 4
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 16
        assert stretch.closure('0') is None, 'closure 0 should be removed'

        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        assert closures[0].shape.equals(Polygon([(0, 0), (0.1, 0), (0.1, 1), (0, 1)]))
        assert closures[1].shape.equals(Polygon([(0.1, 0), (0.2, 0), (0.2, 1), (0.1, 1)]))
        assert closures[2].shape.equals(Polygon([(0.2, 0), (0.3, 0), (0.3, 1), (0.2, 1)]))
        assert closures[3].shape.equals(Polygon([(0.3, 0), (1, 0), (1, 1), (0.3, 1)]))

    def test_cut_box_with_crossing_cutting(self, stretch_box):
        stretch = stretch_box
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(0.1, -1), (0.1, 2)]))
                    .by(LineString([(0.2, -1), (0.2, 2)]))
                    .by(LineString([(-1, 0.5), (2, 0.5)]))
                    .closures())
        assert len(closures) == 6
        assert len(stretch.closures) == 6
        assert len(stretch.pivots) == 12
        assert len(stretch.edges) == 24
        assert stretch.closure('0') is None, 'closure 0 should be removed'

        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.xy)
        assert closures[0].shape.equals(Polygon([(0, 0), (0.1, 0), (0.1, 0.5), (0, 0.5)]))
        assert closures[1].shape.equals(Polygon([(0, 0.5), (0.1, 0.5), (0.1, 1), (0, 1)]))
        assert closures[2].shape.equals(Polygon([(0.1, 0), (0.2, 0), (0.2, 0.5), (0.1, 0.5)]))
        assert closures[3].shape.equals(Polygon([(0.1, 0.5), (0.2, 0.5), (0.2, 1), (0.1, 1)]))
        assert closures[4].shape.equals(Polygon([(0.2, 0), (1, 0), (1, 0.5), (0.2, 0.5)]))
        assert closures[5].shape.equals(Polygon([(0.2, 0.5), (1, 0.5), (1, 1), (0.2, 1)]))

    def test_cut_box_inside(self, stretch_box):
        stretch = stretch_box

        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(0.2, 0.2), (0.5, 0.5)]))
                    .closures())

        assert len(closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 6
        assert len(closures[0].interiors) == 1
        assert closures[0].shape.equals(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)],
                                                [[(0.2, 0.2), (0.5, 0.5), (0.2, 0.2)]]))

    def test_cut_box_to_create_a_crack(self, stretch_box):
        stretch = stretch_box
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(0.5, -1), (0.5, 0.5)]))
                    .closures())
        assert len(closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 7
        assert stretch.closure('0') is None, 'closure 0 should be removed'
        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (0.5, 0), (0.5, 0.5), (0.5, 0),
                                                         (1, 0), (1, 1), (0, 1)]))

    def test_cut_on_hole_to_create_a_crack(self, stretch_box_holes):
        stretch = stretch_box_holes
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(2.5, 2.5), (4, 2.5)]))
                    .closures())

        assert len(closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 15
        assert stretch.closure('0') is None, 'closure 0 should be removed'
        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                                                        [[(3, 3), (3, 2.5), (4, 2.5), (3, 2.5), (3, 2),
                                                          (2, 2), (2, 3), (3, 3)],
                                                         [(8, 6), (9, 6), (9, 5), (8, 5), (8, 6)]]))
        assert len(stretch.closures[0].interiors) == 2
        # check the equality of 2 linear rings might fail due to the order of the points
        # use symmetric_difference to check the equality of 2 linear rings instead
        assert stretch.closures[0].interiors[0].shape.symmetric_difference(
            LinearRing([(3, 2.5), (4, 2.5), (3, 2.5), (3, 2), (2, 2), (2, 3), (3, 3), (3, 2.5)])).area == 0

    def test_cut_into_inner_crack(self, stretch_box_with_inner_crack):
        stretch = stretch_box_with_inner_crack
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(5, -1), (5, 4)]))
                    .closures())
        assert len(closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 15
        assert stretch.closure('0') is None, 'closure 0 should be removed'
        assert stretch.closures[0].shape.equals(Polygon(
            [(0, 0), (5, 0), (5, 3), (3, 3), (3, 6), (3, 3), (5, 3), (5, 4), (5, 3), (5, 8), (5, 3), (5, 0), (10, 0),
             (10, 10), (0, 10)]))
        assert len(stretch.closures[0].interiors) == 0

    def test_cut_into_inner_crack_to_form_2_closures(self, stretch_box_with_exterior_crack):
        stretch = stretch_box_with_exterior_crack
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(5, 5), (11, 5)]))
                    .closures())

        assert len(closures) == 2
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 10
        closures = sorted(stretch.closures, key=lambda c: c.shape.area)
        assert closures[0].shape.equals(Polygon([(5, 0), (10, 0), (10, 5), (5, 5), (5, 0)]))
        assert len(closures[0].interiors) == 0
        assert closures[1].shape.equals(Polygon([(0, 0), (5, 0), (5, 5), (10, 5), (10, 10), (0, 10)]))
        assert len(closures[1].interiors) == 0

    def test_cut_through_2_holes(self, stretch_box_holes):
        stretch = stretch_box_holes
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(3, 2.5), (8, 5.5)]))
                    .closures())
        assert len(closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 16
        assert stretch.closure('0') is None, 'closure 0 should be removed'
        assert stretch.closures[0].shape.equals(Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                                                        [[(3, 3), (3, 2.5), (8, 5.5), (8, 6), (9, 6),
                                                          (9, 5), (8, 5), (8, 5.5), (3, 2.5), (3, 2),
                                                          (2, 2), (2, 3), (3, 3)]]))
        assert len(stretch.closures[0].interiors) == 1
        assert stretch.closures[0].interiors[0].shape.symmetric_difference(
            LinearRing([(3, 3), (3, 2.5), (8, 5.5), (8, 6), (9, 6),
                        (9, 5), (8, 5), (8, 5.5), (3, 2.5), (3, 2),
                        (2, 2), (2, 3), (3, 3)])).area == 0

    def test_cut_through_closure_and_2_holes(self, stretch_box_holes):
        stretch = stretch_box_holes
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(-1, 2.5), (3, 2.5), (8, 5.5), (3, 8.5)]))
                    .closures())
        assert len(closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 17
        assert len(stretch.edges) == 22
        assert stretch.closure('0') is None, 'closure 0 should be removed'
        assert stretch.closures[0].shape.equals(loads(
            'POLYGON ((0 0, 10 0, 10 10, 0 10, 0 2.5, 2 2.5, 2 3, 3 3, 3 2.5, 8 5.5, 3 8.5, 8 5.5, 8 6, 9 6, 9 5, 8 5, 8 5.5, 3 2.5, 3 2, 2 2, 2 2.5, 0 2.5, 0 0))'))
        assert len(stretch.closures[0].interiors) == 0

    def test_cut_across_closure_and_through_holes(self, stretch_box_holes):
        stretch = stretch_box_holes
        closure = stretch.closure('0')
        closures = (Cut([closure])
                    .by(LineString([(-1, 2.5), (3, 2.5), (8, 5.5), (12, 5.5)]))
                    .closures())
        assert len(closures) == 2
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 18
        assert len(stretch.edges) == 24
        assert stretch.closure('0') is None, 'closure 0 should be removed'

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert closures[0].shape.equals(
            loads('POLYGON ((0 0, 10 0, 10 5.5, 9 5.5, 9 5, 8 5, 8 5.5, 3 2.5, 3 2, 2 2, 2 2.5, 0 2.5, 0 0))'))
        assert closures[1].shape.equals(
            loads('POLYGON ((9 6, 9 5.5, 10 5.5, 10 10, 0 10, 0 2.5, 2 2.5, 2 3, 3 3, 3 2.5, 8 5.5, 8 6, 9 6))'))
        assert len(closures[0].interiors) == 0
        assert len(closures[1].interiors) == 0

    def test_cut_across_multiple_closures(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        closures = (Cut(stretch.closures)
                    .by(LineString([(-1, 0.5), (3, 0.5)]))
                    .closures())
        assert len(closures) == 4
        assert len(stretch.closures) == 4
        assert len(stretch.pivots) == 9
        assert len(stretch.edges) == 16
        assert stretch.closure('0') is None, 'closure 0 should be removed'
        assert stretch.closure('1') is None, 'closure 1 should be removed'

        closures = sorted(stretch.closures, key=lambda closure: closure.shape.centroid.xy)
        assert closures[0].shape.equals(Polygon([(0, 0), (1, 0), (1, 0.5), (0, 0.5), (0, 0)]))
        assert closures[1].shape.equals(Polygon([(0, 0.5), (1, 0.5), (1, 1), (0, 1), (0, 0.5)]))
        assert closures[2].shape.equals(Polygon([(1, 0), (2, 0), (2, 0.5), (1, 0.5), (1, 0)]))
        assert closures[3].shape.equals(Polygon([(1, 0.5), (2, 0.5), (2, 1), (1, 1), (1, 0.5)]))

    def test_cargo_inherit_with_cut(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        stretch.closure('0').cargo['test'] = 'closure0'
        stretch.closure('1').cargo['test'] = 'closure1'
        stretch.edge('(3,0)').cargo['test'] = 'edge30'
        stretch.edge('(1,2)').cargo['test'] = 'edge12'
        stretch.edge('(2,1)').cargo['test'] = 'edge21'
        stretch.edge('(4,5)').cargo['test'] = 'edge45'

        closures = (Cut(stretch.closures)
                    .by(LineString([(-1, 0.5), (3, 0.5)]))
                    .closures())

        closures.sort(key=lambda closure: closure.shape.centroid.x)
        assert closures[0].cargo['test'] == 'closure0'
        assert closures[1].cargo['test'] == 'closure0'
        assert closures[2].cargo['test'] == 'closure1'
        assert closures[3].cargo['test'] == 'closure1'

        for edge in stretch.edges_by_query(Point(0, 0.3)):
            assert edge.cargo['test'] == 'edge30'

        for edge in stretch.edges_by_query(Point(0, 0.7)):
            assert edge.cargo['test'] == 'edge30'

        pivot = stretch.pivots_by_query(Point(1, 0.5), MATH_MIDDLE_EPS)[0]
        pivot_id = pivot.id
        assert stretch.edge(f'(1,{pivot_id})').cargo['test'] == 'edge12'
        assert stretch.edge(f'({pivot_id},2)').cargo['test'] == 'edge12'
        assert stretch.edge(f'({pivot_id},1)').cargo['test'] == 'edge21'
        assert stretch.edge(f'(2,{pivot_id})').cargo['test'] == 'edge21'

        for edge in stretch.edges_by_query(Point(2, 0.3)):
            assert edge.cargo['test'] == 'edge45'

        for edge in stretch.edges_by_query(Point(2, 0.7)):
            assert edge.cargo['test'] == 'edge45'