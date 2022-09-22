from shapely.geometry import Point, MultiPoint, Polygon, GeometryCollection


def test_point():
    g = Point(0, 0)
    try:
        assert hash(g)
        return True
    except TypeError:
        return False


def test_multipoint():
    g = MultiPoint([(0, 0)])
    try:
        assert hash(g)
        return True
    except TypeError:
        return False


def test_polygon():
    g = Point(0, 0).buffer(1.0)
    try:
        assert hash(g)
        return True
    except TypeError:
        return False


def test_collection():
    g = GeometryCollection([Point(0, 0)])
    try:
        assert hash(g)
        return True
    except TypeError:
        return False
