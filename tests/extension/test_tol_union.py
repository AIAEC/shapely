from unittest import TestCase

from shapely.extension.util.union import tol_union
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.wkt import loads


class TestUnaryUnion(TestCase):
    def test_tol_union(self):
        eps = 1e-6
        poly1 = Polygon([[0, 0], [1, 0], [1, 1], [0, 1]])
        poly2 = Polygon([[0.5, 0.5], [3, 0], [2, 2], [0.5, 1]])
        poly_collect = [poly1, poly2]
        poly = unary_union(poly_collect)
        test_poly = tol_union(poly_collect, eps)
        self.assertTrue(poly.symmetric_difference(test_poly).area < 5.0)
    def test_tol_union_in_real_case(self):
        eps = 0.0025
        poly1 = loads('POLYGON ((-25.795607122980755 -46.26001625123014, -32.052244870685854 -46.26001625123014, -81.2945027650523 -46.25001625123014, -83.99244856274915 -57.80639430734987, -89.84705799590229 -75.15675023743333, -95.36625146493316 -87.46538643325194, -25.795607122980755 -88.40063101597013, -25.795607122980755 -46.26001625123014))')
        poly2 = loads('POLYGON ((-86.78995562472548 -87.5806783685245, -86.9068999606106 -87.57910627504096, -86.90689996061151 -83.13107905399511, -56.141323530504295 -83.13107905399511, -56.141323530504295 -87.99265829998811, -56.201139923130306 -87.99188805173745, -56.30934701892714 -96.0411593507376, -86.89816273954138 -95.6299510823067, -86.78995562472548 -87.5806783685245))')
        poly_collect = [poly1, poly2]
        poly = unary_union(poly_collect)
        test_poly = tol_union(poly_collect, eps)
        self.assertTrue(poly.symmetric_difference(test_poly).area < 5.0)

    def test_real_case0(self):
        poly0 = loads("POLYGON ((-7.194464434810454 3.8670799192639773, -4.794464434810454 3.8670799192639773, -4.794464434810455 -1.4329200807360225, -7.194464434810455 -1.432920080736022, -7.194464434810454 3.8670799192639773))")
        poly1 = loads("POLYGON ((-4.794464434810454 3.867079919263977, -2.3944644348104536 3.867079919263977, -2.3944644348104545 -1.4329200807360232, -4.794464434810455 -1.4329200807360227, -4.794464434810454 3.867079919263977))")
        poly2 = loads("POLYGON ((-2.3944644348104536 3.8670799192639764, 0.0055355651895466 3.8670799192639764, 0.0055355651895457 -1.4329200807360236, -2.3944644348104545 -1.4329200807360232, -2.3944644348104536 3.8670799192639764))")
        result = tol_union([poly0, poly1, poly2])
        shapely_union = unary_union([poly0, poly1, poly2])
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(shapely_union.area < result.area)
