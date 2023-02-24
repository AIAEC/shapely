from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.model.stretch.stretch_v3 import Stretch, Closure
from shapely.geometry import Polygon, Point


class TestAddingClosure:
    def test_add_closure_to_empty_stretch(self):
        stretch = Stretch()
        assert len(stretch.pivots) == 0
        assert len(stretch.edges) == 0
        assert len(stretch.closures) == 0

        closure = stretch.add_closure(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert closure in stretch.closures

    def test_add_closure_duplicate_to_existed_one(self, stretch_box):
        stretch = stretch_box
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        closure = stretch.add_closure(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1
        assert closure is stretch.closure('0')

    def test_add_closure_almost_attach_to_pivots_and_edges(self, stretch_2_boxes):
        stretch = stretch_2_boxes
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 2

        #         ┌───────────┐
        #         │           │
        #   3     │      2    │     5
        #   ┌─────┴─────┬─────┴─────┐
        #   │    (6)    │    (7)    │
        #   │           │           │
        #   └───────────┴───────────┘
        #   0            1          4

        closure = stretch.add_closure(Polygon([(0.5, 1 + MATH_MIDDLE_EPS), (1.5, 1 + MATH_MIDDLE_EPS),
                                               (1.5, 2), (0.5, 2)]),
                                      dist_tol_to_pivot=2 * MATH_MIDDLE_EPS,
                                      dist_tol_to_edge=2 * MATH_MIDDLE_EPS)
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 15
        assert len(stretch.closures) == 3

        assert stretch.pivot('6').shape.equals(Point(0.5, 1 + MATH_MIDDLE_EPS))
        assert len(stretch.pivot('6').in_edges) == 2
        assert len(stretch.pivot('6').out_edges) == 2
        assert stretch.edge('(6,2)') in stretch.pivot('6').out_edges
        assert stretch.edge('(6,2)').reverse is not None

        assert stretch.pivot('7').shape.equals(Point(1.5, 1 + MATH_MIDDLE_EPS))
        assert len(stretch.pivot('7').in_edges) == 2
        assert len(stretch.pivot('7').out_edges) == 2
        assert stretch.edge('(7,2)') in stretch.pivot('7').out_edges
        assert stretch.edge('(7,2)').reverse is not None

        assert closure.stretch is stretch
        assert stretch.closure('2').shape.equals(Polygon([(0.5, 1 + MATH_MIDDLE_EPS), (1, 1),
                                                          (1.5, 1 + MATH_MIDDLE_EPS), (1.5, 2), (0.5, 2)]))

    def test_add_closure_attach_to_closure_without_hole_and_expand_edge(self, stretch_box):
        stretch = stretch_box
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        new_closure = stretch.add_closure(Polygon([(0.4, 1), (0.6, 1), (0.6, 2), (0.4, 2)]))
        assert isinstance(new_closure, Closure)
        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 10
        assert len(stretch.closures) == 2

        closures = sorted(stretch.closures, key=lambda c: c.shape.centroid.y)
        assert closures[0].shape.equals(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))
        assert closures[1].shape.equals(Polygon([(0.4, 1), (0.6, 1), (0.6, 2), (0.4, 2)]))

    def test_add_closure_attach_to_closure_with_hole_and_expand_edge(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit
        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10
        assert len(stretch.closures) == 1

        new_closure = stretch.add_closure(Polygon([(10, 30), (20, 30), (20, 40), (10, 40)]))
        assert isinstance(new_closure, Closure)
        assert len(stretch.pivots) == 14
        assert len(stretch.edges) == 16
        assert len(stretch.closures) == 2

        closures = stretch.closures
        # exist shared edges
        assert len(set(closures[0].edges).symmetric_difference(closures[1].edges)) > 0

    def test_default_cargo_when_adding_closure(self, stretch_4_dangling_edge):
        stretch = Stretch(default_pivot_cargo_dict={'test': 'pivot'},
                          default_edge_cargo_dict={'test': 'edge'},
                          default_closure_cargo_dict={'test': 'closure'})
        closure = stretch.add_closure(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]))
        assert closure.cargo['test'] == 'closure'

        for closure in stretch.closures:
            assert closure.cargo['test'] == 'closure'

        for edge in stretch.edges:
            assert edge.cargo['test'] == 'edge'

        for pivot in stretch.pivots:
            assert pivot.cargo['test'] == 'pivot'
