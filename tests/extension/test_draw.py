import pytest

from shapely import wkt
from shapely.geometry import Point, LineString, box


@pytest.mark.skip
def test_save_twice_with_same_draw():
    from shapely.extension.draw import Draw
    draw = Draw()
    draw.draw(LineString([(0, 0), (1, 1)])).save('1.png')  # should only have 1 line
    draw.draw(LineString([(0, 0), (1, 0)])).save('2.png')  # should only have 1 line


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


@pytest.mark.skip
def test_draw_text():
    from shapely.extension.draw import Draw
    draw = Draw()
    draw.draw_text('123四五六abc', Point(0, 0), fontsize=10)
    draw.draw_point(Point(0, 0))
    draw.show()


@pytest.mark.skip
def test_draw_polygon_with_hole():
    from shapely.extension.draw import Draw
    poly = wkt.loads(
        "POLYGON ((-210 100, -45 100, -45 -62, -210 -62, -210 100), (-160 60, -97 60, -97 -15, -160 -15, -160 60))")
    Draw().draw(poly).show()
