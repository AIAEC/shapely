from shapely.extension.model.query import Query
from shapely.geometry import Point


def test_query():
    assert not Query([Point(1, 1).buffer(1)], use_rtree=True).intersects(Point(2, 0))
    assert Query([Point(1, 1).buffer(1)], use_rtree=True).intersects(Point(2, 1))

    assert not Query([Point(1, 1).buffer(1)], use_rtree=False).intersects(Point(2, 0))
    assert Query([Point(1, 1).buffer(1)], use_rtree=False).intersects(Point(2, 1))
