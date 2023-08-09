from unittest import TestCase

from shapely import wkt
from shapely.extension.constant import MATH_EPS, COMPARE_EPS, MATH_MIDDLE_EPS
from shapely.extension.geometry.empty import EMPTY_GEOM
from shapely.extension.model.vector import Vector
from shapely.geometry import box, LineString, Polygon, Point
from shapely.wkt import loads


class PolygonExtensionTest(TestCase):
    def test_edge_pair_with(self):
        polygon = box(0, 0, 1, 1)
        self.assertEqual(4, len(list(polygon.ext.edge_pair_with(LineString([(0, 0), (1, 0)])))))

    def test_union(self):
        polygon = box(0, 0, 1, 1)
        large_poly = box(2, -10, 100, 100)
        result = polygon.ext.union(large_poly, direction=Vector(1, 1), dist_tol=2)
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.area > polygon.area + large_poly.area)

    def test_union_without_direction(self):
        polygon0 = loads('POLYGON ((3 8, 5 8, 5 6, 3 6, 3 8))')
        polygon1 = loads('POLYGON ((0 8, 2 10, 3 9, 1 7, 0 8))')
        result = polygon0.ext.union(polygon1, dist_tol=2)
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.area > polygon0.area + polygon1.area)

    def test_cut_not_intersect(self):
        poly1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
        point1 = Point(0, 0)
        vector1 = Vector(1, 1)
        result1 = poly1.ext.cut(point1, vector1, 2.5)
        self.assertLessEqual(abs(result1.area - 2.5), MATH_EPS)

        self.assertTrue(poly1.ext.cut(Point(-1, -1), Vector(-1, -1), 2.5).equals(EMPTY_GEOM))
        self.assertTrue(poly1.ext.cut(Point(-100, -100), Vector(1, 1), 2.5).equals(EMPTY_GEOM))

        poly2 = wkt.loads("POLYGON ((-40 20, -10 20, -10 10, -40 10, -40 20))")
        point2 = Point(0, 0)
        vector2 = Vector(-1, 1)
        result2 = poly2.ext.cut(point2, vector2, 150)
        expect2 = wkt.loads("POLYGON ((-30 10, -20 20, -10 20, -10 10, -30 10))")
        self.assertTrue(expect2.within(result2.buffer(COMPARE_EPS)))
        self.assertTrue(result2.within(expect2.buffer(COMPARE_EPS)))

        vector3 = Vector(0, 1)
        result3 = poly2.ext.cut(point2, vector3, 150)
        expect3 = wkt.loads("POLYGON ((-40 15, -10 15, -10 10, -40 10, -40 15))")
        self.assertTrue(expect3.within(result3.buffer(COMPARE_EPS)))
        self.assertTrue(result3.within(expect3.buffer(COMPARE_EPS)))

        point4 = Point(0, 30)
        vector4 = Vector(-1, -1)
        result4 = poly2.ext.cut(point4, vector4, 150)
        expect4 = wkt.loads("POLYGON ((-30 20, -10 20, -10 10, -20 10, -30 20))")
        self.assertTrue(expect4.within(result4.buffer(COMPARE_EPS)))
        self.assertTrue(result4.within(expect4.buffer(COMPARE_EPS)))

        vector5 = Vector(0, -1)
        result5 = poly2.ext.cut(point4, vector5, 150)
        expect5 = wkt.loads("POLYGON ((-40 15, -40 20, -10 20, -10 15, -40 15))")
        self.assertTrue(expect5.within(result5.buffer(COMPARE_EPS)))
        self.assertTrue(result5.within(expect5.buffer(COMPARE_EPS)))

        point6 = Point(-50, 30)
        vector6 = Vector(1, -1)
        result6 = poly2.ext.cut(point6, vector6, 150)
        expect6 = wkt.loads("POLYGON ((-30 10, -40 10, -40 20, -20 20, -30 10))")
        self.assertTrue(expect6.within(result6.buffer(COMPARE_EPS)))
        self.assertTrue(result6.within(expect6.buffer(COMPARE_EPS)))

        vector7 = Vector(-1, 0)
        result7 = poly2.ext.cut(point2, vector7, 150)
        expect7 = wkt.loads("POLYGON ((-25 20, -10 20, -10 10, -25 10, -25 20))")
        self.assertTrue(expect7.within(result7.buffer(COMPARE_EPS)))
        self.assertTrue(result7.within(expect7.buffer(COMPARE_EPS)))

        vector8 = Vector(1, 0)
        result8 = poly2.ext.cut(point6, vector8, 150)
        expect8 = wkt.loads("POLYGON ((-25 10, -40 10, -40 20, -25 20, -25 10))")
        self.assertTrue(expect8.within(result8.buffer(COMPARE_EPS)))
        self.assertTrue(result8.within(expect8.buffer(COMPARE_EPS)))

    def test_cut_intersect(self):
        poly1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)])
        point1 = Point(1, 1)
        vector1 = Vector(1, 1)
        result1 = poly1.ext.cut(point1, vector1, 1.5)
        expect1 = wkt.loads("POLYGON ((0 2, 1 2, 2 1, 2 0, 0 2))")
        self.assertTrue(expect1.within(result1.buffer(COMPARE_EPS)))
        self.assertTrue(result1.within(expect1.buffer(COMPARE_EPS)))

    def test_cut_special_polygon(self):
        poly1 = Polygon([(0, 0), (0, 2), (1, 2), (1, 1), (2, 1), (2, 2), (3, 2), (3, 0), (0, 0)])
        point1 = Point(1.5, -1)
        vector1 = Vector(0, 1)
        result1 = poly1.ext.cut(point1, vector1, 4)
        expect1 = wkt.loads("POLYGON ((1 1.5, 1 1, 2 1, 2 1.5, 3 1.5, 3 0, 0 0, 0 1.5, 1 1.5))")
        self.assertLessEqual(abs(result1.area - 4), MATH_EPS)
        self.assertTrue(expect1.within(result1.buffer(COMPARE_EPS)))
        self.assertTrue(result1.within(expect1.buffer(COMPARE_EPS)))

        point2 = Point(0, 2)
        vector2 = Vector(0, -1)
        result2 = poly1.ext.cut(point2, vector2, 0.5)
        expect2 = wkt.loads("MULTIPOLYGON (((1 2, 1 1.75, 0 1.75, 0 2, 1 2)), ((3 2, 3 1.75, 2 1.75, 2 2, 3 2)))")
        self.assertLessEqual(abs(result2.area - 0.5), MATH_EPS)
        self.assertTrue(expect2.within(result2.buffer(COMPARE_EPS)))
        self.assertTrue(result2.within(expect2.buffer(COMPARE_EPS)))

    def test_cut_error(self):
        poly = wkt.loads("POLYGON ((6.889720504239981 -42.80172602284849, 18.820037941347525 -44.21685785117151, 17.56299874492298 -48.23793826670277, 16.808053674199545 -54.60216282057748, 16.520757379336782 -54.568084759043224, 16.78582912540839 -52.33375322670993, 15.892093575277002 -52.2277414993698, 15.791971494587973 -53.071824178232404, 16.089882040033835 -53.107161265932326, 15.924975083289002 -54.49741518860746, 9.867442564601175 -53.778892292180345, 10.03234952704169 -52.38863833705605, 10.330260065103731 -52.423975423736124, 10.430382145924124 -51.57989274491312, 9.536647544507044 -51.473881130106115, 9.27161849962796 -53.708217767263676, 7.384845475004496 -53.48441548236126, 7.967909341629519 -48.5688750280149, 7.6704956432863725 -48.533596874428575, 7.830139588600162 -47.18771304395169, 9.478876732602027 -47.310929152949875, 9.5003141358343 -47.08907633809089, 6.920965923657316 -46.783123241198254, 6.343791576380447 -51.649011624939355, 3.3150243141990083 -51.289750041192306, 3.3385824512049034 -51.09114234826111, 2.5441516849248016 -50.99690980052324, 3.3451283298980496 -44.24424836907093, 5.778072532048598 -44.53283554382771, 5.825188805224441 -44.13562016535225, 3.0446811474776028 -43.80580625156443, 3.221367154537291 -42.316248730895275, 3.767538228650565 -42.38103359803345, 3.838212638509871 -41.78521053052369, 3.2920415644038017 -41.72042566325433, 3.951669400732342 -36.15941027331448, 4.497840475039155 -36.224195140607804, 4.568514884844475 -35.62837207294757, 4.0223438105847995 -35.563587205792004, 4.199029852639923 -34.074029390092576, 6.979537510545901 -34.40384330402155, 7.026653783786406 -34.006627925674096, 4.593709580752005 -33.718040750692424, 5.394686225780844 -26.965379328255114, 6.189116992089878 -27.05961187587637, 6.248012333655253 -26.563092652815925, 5.453581567223609 -26.46886010530018, 5.618488503163376 -25.078606453570913, 10.285769196637473 -25.63222268144242, 10.120862262073372 -27.02247632304061, 9.525039193791974 -26.951802001468604, 9.466143852314172 -27.448321224421903, 10.061966920538723 -27.51899554586714, 9.70270533789774 -30.547762798370595, 10.099920716306382 -30.59487907161826, 10.467427530732193 -27.49660010528948, 12.354200555057913 -27.720402398079273, 12.304728585713335 -28.13747755426893, 13.198463186853491 -28.243489169178165, 13.298585267639952 -27.39940649006755, 13.000674733451278 -27.364069403774906, 13.165581663662252 -25.973815788795218, 15.896436413213662 -26.297740061750456, 15.83165154218672 -26.843911167534245, 16.4274746098158 -26.914585577551723, 16.49225948053238 -26.368414473827077, 19.421723366338977 -26.71589705579684, 19.256815960068604 -28.10615059081218, 18.760296720193015 -28.047255246891968, 18.660174639338337 -28.891337926003533, 19.55390921038928 -28.997349537343627, 19.81893958516465 -26.763013430225133, 21.7057112961473 -26.986815576718993, 21.440682287767586 -29.221151838828685, 22.334416889022428 -29.32716345334637, 22.434538969658114 -28.483080774360413, 21.93801974671145 -28.424185432928454, 22.102926674320248 -27.033931851432044, 28.508023657900896 -27.793681663814034, 28.343116734258608 -29.183935221713057, 27.896250422192157 -29.130929531848853, 27.79612834150426 -29.97501221070404, 28.689862942707656 -30.081023825080564, 28.73992386533222 -29.658983478664595, 30.626696935334984 -29.88278577949538, 30.576636012778145 -30.304826126208997, 31.470370614086175 -30.410837740732966, 31.57049269478763 -29.566755061766813, 31.123626387349837 -29.513749372181532, 31.288533316423514 -28.123495825380086, 46.77993106184916 -29.961030301562573, 46.61502413852025 -31.35128379086574, 46.16815782621634 -31.298278100635752, 46.06803574559525 -32.14236077949886, 46.961770346786814 -32.248372394549264, 47.011831270277455 -31.826332039972474, 48.89860434041169 -32.050134339434415, 48.53050857137779 -35.1533785077242, 48.92772394976494 -35.20049478112941, 49.28698553328723 -32.17172752119554, 49.8828086103525 -32.242401931948166, 49.94170395193163 -31.745882709407027, 49.34588087459445 -31.675208298262014, 49.51078779104909 -30.284954809336675, 54.17806850424792 -30.838571039547855, 54.01316156811707 -32.22882469386777, 53.21873080171345 -32.13459214611526, 53.159835460147825 -32.631111369175805, 53.95426622645705 -32.72534391679694, 53.15328958352796 -39.47800533948333, 50.72034538046566 -39.18941816473846, 50.67322910722552 -39.58663354308591, 53.45373673913061 -39.916447453686295, 54.525631959535275 -30.879797784593627, 63.27378888757433 -32.752906663710505, 59.993051494097415 -48.075243703487324, 52.67190827776145 -46.50767929447384, 52.29938801654559 -49.64822422010156, 49.5188803323614 -49.31841030305557, 49.471764059120815 -49.71562568140302, 51.90470826215502 -50.004212856384655, 51.103731617126385 -56.756874278821996, 50.30930085081737 -56.66264173120075, 50.250405509251614 -57.159160954261296, 51.04483627568359 -57.25339350177695, 50.87992933936848 -58.64364715666904, 46.21264873294375 -58.090030982191976, 46.3775555620971 -56.6997772103637, 46.97337872752305 -56.77045163180746, 47.03227406897161 -56.273932409100745, 46.43645090110773 -56.20325798736784, 46.7957125769121 -53.174490737322245, 46.39849712034784 -53.12737445496405, 45.815440844328506 -58.042915599528975, 43.92866025197521 -57.819112416969446, 44.19368929042205 -55.584775968198244, 43.299954689006555 -55.47876435352643, 43.19983260830394 -56.32284703249998, 43.49774315355125 -56.358184120176354, 43.33283621168558 -57.74843789498065, 37.27530267601018 -57.02991487792208, 37.44020962626463 -55.63966107092808, 37.73812016355716 -55.67499815758888, 37.83824224404184 -54.83091547872909, 36.94450764285152 -54.72490386367887, 36.67947861554539 -56.95924035354018, 36.392183301911004 -56.92516240839574, 37.154199682699776 -50.5009566901186, 36.53896207167329 -46.27412934393614, 37.668232028935016 -46.4482436502577, 37.590429145984906 -47.10416355907169, 49.37030466003946 -48.5014503777092, 49.648580057204995 -46.15543997477515, 49.350668523525464 -46.12010276973429, 49.76146861232253 -42.656838350516225, 50.05938014603266 -42.692175555440556, 50.33765556980466 -40.34616492819117, 38.27526064477601 -38.91536680302245, 38.09899949439357 -39.60545833115539, 7.702500310519205 -35.94955763044962, 6.889720504239981 -42.80172602284849))")
        vector = Vector.from_angle(0)
        point = wkt.loads("POINT (-359.5416518733821 -39.63072807776144)")
        target_area = 138 * 1.25
        with self.assertRaises(ValueError):
            poly = poly.ext.cut(point, vector, target_area)
        poly = poly.ext.cut(point, vector, target_area, tolerance=MATH_MIDDLE_EPS)
        assert poly.area - target_area < MATH_MIDDLE_EPS

    def test_convex_points_from_exterior(self):
        invalid_poly = Polygon([(0, 0), (1, 0), (0, 1), (1, 1)])
        empty_points = invalid_poly.ext.convex_points("exterior")
        self.assertEqual(0, len(empty_points))

        # with duplicate coords and concave coords
        poly = Polygon([(0, 0), (2, 0), (2, 2), (1, 2), (1, 1), (0, 1), (0, 1), (0, 1)])
        convex_points = poly.ext.convex_points("exterior")
        self.assertEqual(5, len(convex_points))
        self.assertTrue(Point(0, 0) in convex_points)
        self.assertTrue(Point(2, 0) in convex_points)
        self.assertTrue(Point(2, 2) in convex_points)
        self.assertTrue(Point(1, 2) in convex_points)
        self.assertTrue(Point(0, 1) in convex_points)

    def test_convex_points_from_interior(self):
        invalid_poly = Polygon([(0, 0), (4, 0), (4, 4), (0, 4)], [[(0, 0), (2, 0), (2, 2)]])
        empty_points = invalid_poly.ext.convex_points("interiors")
        self.assertEqual(0, len(empty_points))

        interior_is_concave = Polygon([(0, 0), (9, 0), (9, 9), (0, 9)], [[(4, 2), (6, 6), (1, 6)]])
        empty_convex = interior_is_concave.ext.convex_points("interiors")
        self.assertEqual(0, len(empty_convex))

        interior_has_convex = Polygon([(0, 0), (9, 0), (9, 9), (0, 9)], [[(1, 1), (3, 3), (5, 1), (5, 5), (1, 5)]])
        one_convex = interior_has_convex.ext.convex_points("interiors")
        self.assertEqual(1, len(one_convex))
        self.assertTrue(Point(3, 3) in one_convex)

    def test_convex_points_from_both(self):
        poly_without_interiors = Polygon([(0, 0), (9, 0), (9, 9)])
        only_exterior = poly_without_interiors.ext.convex_points("both")
        self.assertEqual(3, len(only_exterior))
        self.assertTrue(Point(0, 0) in only_exterior)
        self.assertTrue(Point(9, 0) in only_exterior)
        self.assertTrue(Point(9, 9) in only_exterior)

        poly = Polygon([(0, 0), (9, 0), (9, 9), (0, 9)], [[(1, 1), (3, 3), (5, 1), (5, 5), (1, 5)]])
        both_with_convex = poly.ext.convex_points("both")
        self.assertEqual(5, len(both_with_convex))
        self.assertTrue(Point(0, 0) in both_with_convex)
        self.assertTrue(Point(9, 0) in both_with_convex)
        self.assertTrue(Point(9, 9) in both_with_convex)
        self.assertTrue(Point(0, 9) in both_with_convex)
        self.assertTrue(Point(3, 3) in both_with_convex)

    def test_concave_points_from_exterior(self):
        invalid_poly = Polygon([(0, 0), (1, 0), (0, 1), (1, 1)])
        invalid_res = invalid_poly.ext.concave_points("exterior")
        self.assertEqual(len(invalid_res), 0)

        poly_with_complex_concave = Polygon(
            [[0, 0], (8, 0), (4, 4), (9, 9), (7, 9), (7, 10), (6, 10), (3, 10), (3, 9), (3, 8), (4, 8), (4, 8), (4, 8)])
        concave_points = poly_with_complex_concave.ext.concave_points("exterior")
        self.assertEqual(3, len(concave_points))
        self.assertTrue(Point(4, 4) in concave_points)
        self.assertTrue(Point(7, 9) in concave_points)
        self.assertTrue(Point(4, 8) in concave_points)

    def test_concave_points_from_interiors(self):
        invalid_poly = Polygon([(0, 0), (4, 0), (4, 4), (0, 4)], [[(0, 0), (2, 0), (2, 2)]])
        empty_points = invalid_poly.ext.concave_points("interiors")
        self.assertEqual(0, len(empty_points))

        interior_is_concave = Polygon([(0, 0), (9, 0), (9, 9), (0, 9)], [[(2, 2), (4, 2), (3, 5)]])
        concave_points = interior_is_concave.ext.concave_points("interiors")
        self.assertEqual(3, len(concave_points))
        self.assertTrue(Point(2, 2) in concave_points)
        self.assertTrue(Point(4, 2) in concave_points)
        self.assertTrue(Point(3, 5) in concave_points)

        interiors_are_concave = Polygon([(0, 0), (9, 0), (9, 9), (0, 9)],
                                        [[(2, 2), (4, 2), (3, 5)], [(5, 2), (7, 2), (6, 6)]])
        concave_points = interiors_are_concave.ext.concave_points("interiors")
        self.assertEqual(6, len(concave_points))
        self.assertTrue(Point(2, 2) in concave_points)
        self.assertTrue(Point(4, 2) in concave_points)
        self.assertTrue(Point(3, 5) in concave_points)
        self.assertTrue(Point(5, 2) in concave_points)
        self.assertTrue(Point(7, 2) in concave_points)
        self.assertTrue(Point(6, 6) in concave_points)

    def test_concave_points_from_both(self):
        poly_without_interiors = Polygon([(0, 0), (9, 0), (9, 9)])
        empty = poly_without_interiors.ext.concave_points("both")
        self.assertEqual(0, len(empty))

        poly = Polygon([(0, 0), (9, 0), (9, 9), (7, 8), (6, 9), (0, 9)], [[(2, 2), (4, 2), (3, 5)]])
        both_with_concave = poly.ext.concave_points("both")
        self.assertEqual(4, len(both_with_concave))
        self.assertTrue(Point(2, 2) in both_with_concave)
        self.assertTrue(Point(4, 2) in both_with_concave)
        self.assertTrue(Point(3, 5) in both_with_concave)
        self.assertTrue(Point(7, 8) in both_with_concave)

    def test_is_convex(self):
        assert box(0, 0, 1, 1).ext.ccw().ext.is_convex
        assert Polygon([(0, 0), (0, 1), (1, 1), (1, 0)]).ext.is_convex
        assert not box(0, 0, 10, 10).difference(box(-1, -1, 1, 1)).ext.is_convex

        assert Polygon([(0, 0), (1, 0), (1, 0.5), (1, 1), (0, 1)]).ext.is_convex
        assert Polygon([(0, 1), (1, 1), (1, 0.5), (1, 0), (0, 0)]).ext.is_convex
