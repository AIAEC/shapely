from shapely.extension.model.mould import mould
from shapely.geometry import Point, box, LineString, Polygon


def test_mould_of_point():
    point = Point(0, 0)
    geom = mould(point, margin=1)
    assert geom.equals(box(-1, -1, 1, 1))


def test_mould_of_line():
    line = LineString([(0, 0), (1, 1)])
    geom = mould(line, margin=1)
    assert geom.equals(box(-1, -1, 2, 2))


def test_mould_of_polygon():
    poly = box(0, 0, 1, 1)
    geom = mould(poly, margin=1)
    assert geom.equals(Polygon([(-1, -1), (2, -1), (2, 2), (-1, 2)], [[(0, 0), (1, 0), (1, 1), (0, 1)]]))
