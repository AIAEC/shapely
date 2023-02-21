import pytest

from shapely.extension.draw import Draw
from shapely.geometry import Point, LineString, box


@pytest.mark.skip
def test_draw_point():
    Draw().draw(Point(0, 0)).show()


@pytest.mark.skip
def test_draw_line():
    Draw().draw(LineString([(0, 0), (1, 1)])).show()


@pytest.mark.skip
def test_draw_polygon():
    Draw().draw(box(-1, -1, 1, 1)).show()
