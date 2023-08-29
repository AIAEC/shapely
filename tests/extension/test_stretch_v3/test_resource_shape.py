from shapely.geometry import Point, LineString, LinearRing, Polygon


class TestResourceShape:
    def test_pivot_shape(self, stretch_box):
        assert stretch_box.pivot('0').shape.equals(Point(0, 0))

    def test_edge_shape(self, stretch_box):
        assert stretch_box.edge('(0,1)').shape.equals(LineString([(0, 0), (1, 0)]))

    def test_edge_seq_shape(self, stretch_box):
        assert stretch_box.closure('0').exterior.shape.equals(LinearRing([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]))

    def test_closure_shape(self, stretch_box_holes):
        assert stretch_box_holes.closure('0').shape.equals(
            Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                    [
                        [(2, 2), (2, 3), (3, 3), (3, 2)],
                        [(8, 6), (9, 6), (9, 5), (8, 5)]
                    ])
        )

    def test_closure_shape_with_inner_crack(self, stretch_box_with_inner_crack):
        poly = stretch_box_with_inner_crack.closure('0').real_shape
        assert len(poly.interiors) == 1
        assert not poly.is_valid
        assert poly.equals(
            Polygon([(0, 0), (10, 0), (10, 10), (0, 10)],
                    [[(8, 3), (3, 3), (3, 6), (3, 3)]])
        )
