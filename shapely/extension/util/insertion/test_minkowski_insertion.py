from shapely.extension.util.insertion.minkowski_insertion import MinkowskiInsertion
from shapely.geometry import Polygon
from shapely.wkt import loads


def test_insert_convex_into_non_hole_concave():
    convex = loads('POLYGON ((-0.1 1.2, -0.9 -0.6, 1.3 -0.3, -0.1 1.2))')
    non_hole_concave = loads(
        'POLYGON ((-3.3 5.9, 5.6 6.1, 5.6 7.1, -4.7 7.1, -8.1 0.9, -0.2 2, -0.2 3.1, -5.4 2.4, -3.3 5.9))')

    space = non_hole_concave.envelope
    res = MinkowskiInsertion(convex).of(space=space, obstacle=non_hole_concave)
    assert len(res) == 2
    for poly in res:
        assert isinstance(poly, Polygon)
        assert poly.is_valid
        assert not poly.is_empty


def test_insert_concave_into_polygon_with_holes():
    concave = loads("POLYGON ((-50 60, 93 45, -20 10, 60 -60, -80 -40, -50 60))")
    poly_with_hole = loads(
        "POLYGON ((80 370, -56 155, 216 -14, 400 80, 410 350, 80 370), (160 320, 362 215, 180 80, 50 170, 160 320))")

    space = poly_with_hole.envelope
    res = MinkowskiInsertion(concave).of(space=space, obstacle=poly_with_hole)
    assert len(res) == 4
    for poly in res:
        assert isinstance(poly, Polygon)
        assert poly.is_valid
        assert not poly.is_empty
