from shapely.geometry import LineString, Polygon


class TestSplit:
    def test_split_across_stretch_box(self, stretch_box):
        stretch = stretch_box

        assert len(stretch.closures) == 1
        closure = stretch.closures[0]

        new_closures = closure.split(LineString([(0.5, -1), (0.5, 2)]))
        assert len(new_closures) == 2
        assert len(stretch.closures) == 2

        assert closure not in stretch.closures
        assert all(new_closure in stretch.closures for new_closure in new_closures)

        new_closures.sort(key=lambda c: c.shape.centroid.x)
        assert new_closures[0].shape.equals(Polygon([(0, 0), (0.5, 0), (0.5, 1), (0, 1)]))
        assert new_closures[1].shape.equals(Polygon([(0.5, 0), (1, 0), (1, 1), (0.5, 1)]))

    def test_split_with_line_not_go_across_stretch_box(self, stretch_box):
        stretch = stretch_box

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        closure = stretch.closures[0]

        new_closures = closure.split(LineString([(0.5, -1), (0.5, 0.5)]))
        assert len(new_closures) == 1
        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5

        assert closure not in stretch.closures
        assert all(new_closure in stretch.closures for new_closure in new_closures)

        assert new_closures[0].shape.equals(Polygon([(0, 0), (0.5, 0), (1, 0), (1, 1), (0, 1)]))

    def test_split_with_line_go_to_the_interior_and_form_new_closure(self, stretch_box_with_exterior_crack):
        stretch = stretch_box_with_exterior_crack

        assert len(stretch.closures) == 1
        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 7

        closure = stretch.closures[0]
        new_closures = closure.split(LineString([(4, 5), (11, 5)]))
        assert closure not in stretch.closures
        assert all(new_closure in stretch.closures for new_closure in new_closures)

        assert len(new_closures) == 2
        assert len(stretch.closures) == 2
        assert len(stretch.pivots) == 7
        assert len(stretch.edges) == 10

        new_closures.sort(key=lambda c: c.shape.centroid.x)
        assert len(new_closures[0].interiors) == 0
        assert new_closures[0].shape.equals(Polygon([(0, 0), (5, 0), (5, 5), (10, 5), (10, 10), (0, 10)]))

        assert len(new_closures[1].interiors) == 0
        assert new_closures[1].shape.equals(Polygon([(5, 0), (10, 0), (10, 5), (5, 5)]))
