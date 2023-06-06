from typing import List

import shapely.wkt
from shapely.geometry import box, Polygon
from shapely.ops import unary_union


class TestConvexPartition:

    @staticmethod
    def do_test_partition(polygon_to_partition: Polygon):
        partitions: List[Polygon] = polygon_to_partition.ext.partitions()
        assert isinstance(partitions, List)
        assert all(isinstance(p, Polygon) for p in partitions)
        assert all(p.is_valid for p in partitions)
        assert all(p.convex_hull.ext.similar(p, area_diff_tol=1e-10) for p in partitions)
        assert polygon_to_partition.ext.similar(unary_union(partitions), area_diff_tol=1e-10)

    def test_simple_box(self):
        b = box(0, 0, 1, 1)
        self.do_test_partition(b)

    def test_concave_poly(self):
        concave = box(0, 0, 10, 10).difference(box(4, 5, 6, 100))
        self.do_test_partition(concave)

    def test_complicated_poly(self):
        poly = shapely.wkt.loads(
            "POLYGON ((-27.87559515123369 67.39210905393861, -27.87559515123369 58.89210905393861, -31.62559515123369 58.89210905393861, -31.62553995498785 59.192090643904976, -41.37559515120969 59.192090643904976, -42.925595151647435 58.14210905361847, -42.92559515155779 55.192109054142065, -42.32559515137643 55.19210905423586, -42.325595151396 43.94210905402929, -50.62559515142392 43.942109054063394, -50.625595153368785 51.29210905372156, -52.8255951511259 51.29210905372156, -52.8255951511259 50.21381793866988, -62.77559511282139 50.21381793866988, -62.77559515118736 66.06360796426543, -62.77559511282139 72.66381793834944, -54.125595151130554 72.66381803511706, -54.125595151130554 81.01386359353512, -35.97559515086023 81.01386359353512, -35.97559515086011 81.4138179800027, -34.775595150860234 81.4138179800027, -34.775595150860234 67.29210905393859, -28.575595151233692 67.29210905393859, -28.575595151233692 67.39210905393861, -27.87559515123369 67.39210905393861))")
        self.do_test_partition(poly)
