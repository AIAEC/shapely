import pytest

from shapely.geometry import Point, LineString, box


@pytest.mark.skip
def test_draw_point():
    from shapely.extension.draw import Draw
    Draw().draw(Point(0, 0)).show()


@pytest.mark.skip
def test_draw_line():
    from shapely.extension.draw import Draw
    Draw().draw(LineString([(0, 0), (1, 1)])).show()


@pytest.mark.skip
def test_draw_polygon():
    from shapely.extension.draw import Draw
    Draw().draw(box(-1, -1, 1, 1)).show()
