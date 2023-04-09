import pytest

from shapely.extension.util.inscribed_rectangle import InscribedRectangle
from shapely.geometry import box, LineString
from shapely.wkt import loads


@pytest.fixture
def polygon0():
    return loads('POLYGON ((520 470, 555 404, 400 380, 400 210, 450 150, 750 150, 700 500, 520 470))')


@pytest.fixture
def start_line0_for_poly0():
    return loads('LINESTRING (400 170, 800 170)')


def test_polygon_with_holes():
    poly = box(0, 0, 100, 100).difference(box(10, 10, 90, 90))
    result = InscribedRectangle(poly).by_straight_line(LineString([(0, 0), (100, 0)]))
    assert len(result) > 0


def test_inscribed_rectangle_by_line_on_boundary():
    rects = InscribedRectangle(box(0, 0, 100, 100)).by_straight_line(LineString([(0, 0), (100, 0)]))
    assert len(rects) == 1
    assert rects[0].area == 10000


def test_inscribed_rectangle_by_outer_line():
    rects = InscribedRectangle(box(0, 0, 100, 100)).by_straight_line(LineString([(101, 0), (101, 100)]))
    assert rects == []


def test_normal_case(polygon0, start_line0_for_poly0):
    rects = InscribedRectangle(polygon0).by_straight_line(start_line0_for_poly0)
    assert len(rects) == 5
