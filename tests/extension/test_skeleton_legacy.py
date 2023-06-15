import pytest

from shapely.extension.model.skeleton_legacy import skeletonize, Skeleton
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


def test_skeletonize_of_complex_multi_branch_poly():
    poly = loads(
        'POLYGON ((29.722578163148142 -1132.348444800812, 29.222578165736753 -1132.348393921257, 29.2226086934699 -1132.04839392281, 29.97260868958675 -1132.048470242143, 29.97221182905778 -1135.9484702219509, 34.02221180808917 -1135.948882346346, 34.02249673359713 -1133.1488823608431, 34.272496732302706 -1133.14890780062, 34.27209987177374 -1137.048907780428, 34.82209986892622 -1137.048963747939, 34.82207442914869 -1137.298963746645, 34.02207443329063 -1137.298882339356, 34.022181280356136 -1136.2488823447932, 28.272181310126562 -1136.248297229911, 28.27180480141961 -1139.948297210754, 27.47180480556155 -1139.9482158034662, 27.471830245339078 -1139.6982158047601, 27.97183024275035 -1139.698266684315, 27.972181311679773 -1136.248266702177, 24.37218133031856 -1136.247900369382, 24.37183026138926 -1139.697900351519, 24.971830258282722 -1139.697961406985, 24.971804818505188 -1139.947961405691, 23.67180482523586 -1139.9478291188482, 23.67183026501338 -1139.697829120142, 24.07183026294247 -1139.697869823786, 24.07222203551582 -1135.84786984372, 29.722222006263213 -1135.848444782691, 29.722578163148142 -1132.348444800812))')
    lines = skeletonize(poly)
    assert lines
    assert all(poly.covers(line) for line in lines)


class TestSkeleton:
    def test_trunk_segments_of_polygon(self):
        poly = loads('POLYGON ((100 300, 100 200, 200 200, 200 100, 300 100, 300 300, 100 300))')
        skeleton = Skeleton(poly)
        trunk_segments = skeleton.trunk_segments()
        assert len(trunk_segments) == 2
        assert all(seg.within(poly) for seg in trunk_segments)

    def test_trunks_of_polygon(self):
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
