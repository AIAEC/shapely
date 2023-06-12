from shapely.extension.util.regularize import regularize
from shapely.geometry import Polygon
from shapely.wkt import loads


def test_regularize_simple_polygon():
    poly = loads('POLYGON ((140 320, 51 245, 80 150, 210 130, 180 230, 280 240, 280 90, 410 90, 410 300, 140 320))')
    res = regularize(poly)
    assert isinstance(res, Polygon)
    assert res.is_valid


def test_regularize_poly_with_holes():
    poly = loads('POLYGON ((140 320, 51 245, 80 150, 210 130, 180 230, 280 240, 280 90, 410 90, 410 300, 140 320), (120 260, 94 226, 110 200, 150 200, 150 210, 155 252, 120 260), (360 250, 327 145, 370 130, 370 220, 360 250))')
    res = regularize(poly)
    assert isinstance(res, Polygon)
    assert res.is_valid
    assert len(res.interiors) == 2