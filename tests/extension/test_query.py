from shapely.extension.model.query import Query, SeqQueryContainer
from shapely.geometry import Point, box
from shapely.strtree import STRtree


def test_diff_query_container():
    assert not Query([Point(1, 1).buffer(1)], container_type=SeqQueryContainer).intersects(Point(2, 0))
    assert Query([Point(1, 1).buffer(1)], container_type=SeqQueryContainer).intersects(Point(2, 1))

    assert not Query([Point(1, 1).buffer(1)], container_type=STRtree).intersects(Point(2, 0))
    assert Query([Point(1, 1).buffer(1)], container_type=STRtree).intersects(Point(2, 1))


def test_query_intersects():
    assert not Query([Point(1, 1).buffer(1)]).intersects(Point(2, 0))
    assert Query([Point(1, 1).buffer(1)]).intersects(Point(2, 1))


def test_query_covered_by():
    query = Query([box(0, 0, 1, 1), box(1, 1, 2, 2)])
    result = query.covered_by(box(-0.1, -0.1, 1.1, 1.1))
    assert len(result) == 1
    assert result[0].equals(box(0, 0, 1, 1))

    result = query.covered_by(Point(0.5, 0.5))
    assert len(result) == 0


def test_query_covers():
    query = Query([box(0, 0, 1, 1), box(1, 1, 2, 2)])
    result = query.covers(Point(0.5, 0.5))
    assert len(result) == 1
    assert result[0].equals(box(0, 0, 1, 1))

    result = query.covers(box(-0.1, -0.1, 1.1, 1.1))
    assert len(result) == 0
