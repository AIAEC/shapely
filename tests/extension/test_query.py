from dataclasses import dataclass

import pytest

from shapely.extension.model.query import Query, SeqQueryContainer
from shapely.extension.util.func_util import lmap
from shapely.geometry import Point, box, Polygon
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


def test_query_add():
    query = Query([box(0, 0, 1, 1), box(1, 1, 2, 2)])
    query._db._deleted = [box(2, 2, 3, 3), box(3, 3, 4, 4)]
    assert len(query._db._added) == 0
    assert len(query._db._deleted) == 2

    query.add(box(0, 0, 1, 1))
    assert len(query._db._added) == 0
    assert len(query._db._deleted) == 2
    query.add(box(0, 0, 2, 2))
    assert len(query._db._added) == 1
    assert len(query._db._deleted) == 2

    query.add(box(2, 2, 3, 3))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 1

    query._db._deleted.append(box(0, 0, 1, 1))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 2

    query.add(box(0, 0, 1, 1))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 1

    query._db._deleted.append(box(2, 2, 3, 3))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 2

    query.add(box(2, 2, 3, 3))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 1

    query._db._deleted.extend([box(2, 2, 3, 3), box(2, 2, 3, 3), box(2, 2, 3, 3)])
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 4

    query.add(box(2, 2, 3, 3))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 1


def test_query_remove():
    query = Query([box(0, 0, 1, 1), box(1, 1, 2, 2), box(2, 2, 3, 3), box(3, 3, 4, 4)])
    query._db._added = [box(0, 0, 1, 1), box(1, 1, 2, 2)]
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 0

    query.remove(box(3, 3, 4, 4))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 1

    query.remove(box(4, 4, 5, 5))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 1

    query._db._added.append(box(3, 3, 4, 4))
    assert len(query._db._added) == 3
    assert len(query._db._deleted) == 1

    query.remove(box(3, 3, 4, 4))
    assert len(query._db._added) == 2
    assert len(query._db._deleted) == 1

    query.remove(box(1, 1, 2, 2))
    assert len(query._db._added) == 1
    assert len(query._db._deleted) == 2

    query._db._added.extend([box(3, 3, 4, 4), box(3, 3, 4, 4), box(3, 3, 4, 4)])
    assert len(query._db._added) == 4
    assert len(query._db._deleted) == 2

    query.remove(box(3, 3, 4, 4))
    assert len(query._db._added) == 1
    assert len(query._db._deleted) == 2


def test_query_query():
    query = Query([box(0, 0, 1, 1), box(1, 1, 2, 2), box(2, 2, 3, 3), box(3, 3, 4, 4)])
    result = query.intersects(box(0, 0, 0.9, 0.9))
    assert len(result) == 1

    query.remove(box(0, 0, 1, 1))
    result = query.intersects(box(0, 0, 0.9, 0.9))
    assert len(result) == 0

    query.add(box(0, 0, 1, 1))
    result = query.intersects(box(0, 0, 0.9, 0.9))
    assert len(result) == 1


def test_query_items():
    query = Query([box(0, 0, 1, 1), box(1, 1, 2, 2), box(2, 2, 3, 3), box(3, 3, 4, 4)])
    result = query.items()
    assert len(result) == 4

    query._db._deleted = [box(0, 0, 1, 1)]
    result = query.items()
    assert len(result) == 3

    query._db._deleted.append(box(0, 0, 1, 1))
    result = query.items()
    assert len(result) == 3

    query._db._added.append(box(0, 0, 1, 1))
    result = query.items()
    assert len(result) == 4

    query._db._added.append(box(0, 0, 1, 1))
    result = query.items()
    assert len(result) == 4

    query._db._deleted = []
    result = query.items()
    assert len(result) == 4

    query._db._added = [box(4, 4, 5, 5)]
    result = query.items()
    assert len(result) == 5

    query._db._added = [box(4, 4, 5, 5), box(5, 5, 6, 6)]
    result = query.items()
    assert len(result) == 6


def test_query_from_obj():
    @dataclass
    class Test:
        a: Polygon

    tests = lmap(Test, [box(0, 0, 1, 1), box(2, 0, 3, 1)])

    with pytest.raises(TypeError):
        Query(tests)

    query = Query(tests, key=lambda t: t.a)
    result = query.intersects(Point(0, 0))
    assert len(result) == 1
    assert isinstance(result[0], Test)
    assert box(0, 0, 1, 1).equals(result[0].a)
