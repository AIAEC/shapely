from shapely.geometry import LinearRing


class TestSimplify:
    def test_simplify_closure(self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure
        closure = stretch.closures[0]
        another_closure = stretch.closures[1]

        assert len(closure.exterior) == 6
        assert len(another_closure.exterior) == 6

        closure.simplify()

        assert len(closure.exterior) == 4
        assert closure.exterior.shape.equals(LinearRing([(0, 0), (30, 0), (30, 20), (0, 20)]))

        assert len(another_closure.exterior) == 4
        assert another_closure.exterior.shape.equals(LinearRing([(0, 0), (0, -10), (30, -10), (30, 0)]))

    def test_simplify_closure_interior(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        closure = stretch.closures[0]
        assert len(closure.interiors) == 1
        interior = closure.interiors[0]
        assert len(interior) == 6

        closure.simplify()
        assert len(closure.interiors) == 1
        interior = closure.interiors[0]
        assert len(interior) == 4
        assert interior.shape.equals(LinearRing([(5, 25), (25, 25), (25, 20), (5, 20)]))
