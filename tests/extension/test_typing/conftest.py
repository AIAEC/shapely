import pytest as pytest

from shapely.geometry import Point, LineString, Polygon, box, MultiPoint, MultiLineString, MultiPolygon, \
    GeometryCollection


@pytest.fixture
def point() -> Point:
    return Point(1, 1)


@pytest.fixture
def line() -> LineString:
    return LineString([(0, 0), (1, 1)])


@pytest.fixture
def polygon() -> Polygon:
    return box(0, 0, 1, 1)


@pytest.fixture
def multi_point() -> MultiPoint:
    return MultiPoint([Point(0, 0), Point(1, 1)])


@pytest.fixture
def multi_linestring() -> MultiLineString:
    return MultiLineString([LineString([(0, 0), (1, 1)]),
                            LineString([(1, 1), (0, 1)])])


@pytest.fixture
def multi_polygon() -> MultiPolygon:
    return MultiPolygon([box(0, 0, 1, 1), box(1, 1, 2, 2)])


@pytest.fixture
def geometry_collection(point, line, polygon) -> GeometryCollection:
    return GeometryCollection([point, line, polygon])
