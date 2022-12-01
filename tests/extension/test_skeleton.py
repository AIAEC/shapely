import pytest

from shapely.extension.model.skeleton import skeletonize, Skeleton
from shapely.geometry import Polygon, LineString
from shapely.wkt import loads


def test_skeletonize_of_simple_polygon():
    poly = loads('POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300))')
    lines = skeletonize(poly)
    assert len(lines) == 8
    assert all(poly.covers(line) for line in lines)


def test_skeletonize_of_simple_polygon_with_holes():
    poly = loads(
        'POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300), (120 280, 120 210, 200 210, 200 280, 120 280), (220 290, 220 240, 280 240, 280 290, 220 290), (220 210, 290 210, 290 110, 220 110, 220 210))')
    lines = skeletonize(poly)
    assert lines
    assert all(poly.covers(line) for line in lines)


def test_skeletonize_of_non_simple_polygon():
    with pytest.raises(ValueError):
        skeletonize(loads('POLYGON ((150 300, 150 250, 200 250, 150 280, 200 300, 150 300))'))

    with pytest.raises(ValueError):
        skeletonize(Polygon())

    with pytest.raises(ValueError):
        skeletonize(Polygon([(0, 0), (2, 0), (1, 1), (0, -1)]))


class TestSkeleton:
    def test_trunk_segments_of_polygon(self):
        poly = loads('POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300))')
        skeleton = Skeleton(poly)
        trunk_segments = skeleton.trunk_segments()
        assert len(trunk_segments) == 2
        assert all(seg.within(poly) for seg in trunk_segments)

    def tets_trunks_of_polygon(self):
        poly = loads('POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300))')
        skeleton = Skeleton(poly)
        trunks = skeleton.trunks()
        assert len(trunks) == 1
        assert trunks[0].equals(LineString([(150, 250), (250, 250), (250, 150)]))

    def test_full_segments_of_polygon(self):
        poly = loads('POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300))')
        skeleton = Skeleton(poly)
        trunks = skeleton.full_segments()
        assert len(trunks) == 8

    def test_branch_segments_of_polygon(self):
        poly = loads('POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300))')
        skeleton = Skeleton(poly)
        trunks = skeleton.branch_segments()
        assert len(trunks) == 6
