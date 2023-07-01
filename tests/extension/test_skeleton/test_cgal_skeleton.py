import pytest

from shapely.extension.model.skeleton.cgal_skeleton import CgalSkeleton as Skeleton
from shapely.geometry import LineString, Polygon
from shapely.wkt import loads


@pytest.fixture
def simple_poly() -> Polygon:
    return loads('POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300))')


@pytest.fixture
def poly_with_holes() -> Polygon:
    return loads(
        'POLYGON ((210 360, 30 290, 30 100, 170 30, 150 150, 350 150, 290 30, 400 30, 450 230, 378 365, 210 360), (200 310, 110 280, 64 154, 110 100, 130 240, 350 250, 390 180, 420 220, 365 323, 200 310), (210 200, 210 180, 340 180, 330 220, 210 200))')


@pytest.fixture
def complex_poly0() -> Polygon:
    return loads(
        'POLYGON ((651.5863368575259 80.22196853466632, 650.7416117319614 79.37797631322371, 650.7394911998296 79.38009842108187, 650.7394904116246 79.38009763356077, 650.4571187632531 79.66267910682919, 649.5383342155666 78.74389455914276, 649.1848984422387 79.09716418949293, 650.1034821363093 80.01614926107754, 650.4571187630206 79.66267910706185, 649.7499086557777 80.37041472842321, 650.5942732131804 81.21404669457891, 651.5863368575259 80.22196853466632))')


class TestSkeletonForSimpleCase:
    def test_trunk_segments_of_polygon(self, simple_poly):
        poly = simple_poly
        skeleton = Skeleton(poly)
        trunk_segments = skeleton.trunk_segments()
        assert len(trunk_segments) == 2
        assert all(seg.within(poly) for seg in trunk_segments)

    def test_trunks_of_polygon(self, simple_poly):
        poly = simple_poly
        skeleton = Skeleton(poly)
        trunks = skeleton.trunks()
        assert len(trunks) == 1
        assert trunks[0].equals(LineString([(150, 250), (250, 250), (250, 150)]))

    def test_full_segments_of_polygon(self, simple_poly):
        poly = simple_poly
        skeleton = Skeleton(poly)
        trunks = skeleton.full_segments()
        assert len(trunks) == 8

    def test_branch_segments_of_polygon(self, simple_poly):
        poly = simple_poly
        skeleton = Skeleton(poly)
        trunks = skeleton.branch_segments()
        assert len(trunks) == 6


class TestSkeletonForPolygonWithHoles:
    def test_full_segments_of_polygon(self, poly_with_holes):
        poly = poly_with_holes
        skeleton = Skeleton(poly)
        trunks = skeleton.full_segments()
        assert len(trunks) == 49

    def test_trunk_segments_of_polygon(self, poly_with_holes):
        poly = poly_with_holes
        skeleton = Skeleton(poly)
        trunks = skeleton.trunk_segments()
        assert len(trunks) == 26

    def test_trunk_of_polygon(self, poly_with_holes):
        poly = poly_with_holes
        skeleton = Skeleton(poly)
        trunks = skeleton.trunks()
        assert len(trunks) == 5


class TestSkeletonForComplexPolygon0:
    def test_full_segments_of_polygon(self, complex_poly0):
        poly = complex_poly0
        skeleton = Skeleton(poly)
        trunks = skeleton.trunks()
        assert len(trunks) == 3
