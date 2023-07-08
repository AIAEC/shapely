from shapely.extension.util.insertion.minkowski_insertion import MinkowskiInsertion
from shapely.wkt import loads


def test_insert_convex_into_non_hole_concave():
    convex = loads('POLYGON ((-0.1 1.2, -0.9 -0.6, 1.3 -0.3, -0.1 1.2))')
    non_hole_concave = loads('POLYGON ((-3.3 5.9, 5.6 6.1, 5.6 7.1, -4.7 7.1, -8.1 0.9, -0.2 2, -0.2 3.1, -5.4 2.4, -3.3 5.9))')

    space = non_hole_concave.envelope
    res = MinkowskiInsertion(convex).of(space=space, obstacle=non_hole_concave)
    assert res