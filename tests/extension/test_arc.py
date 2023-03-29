from copy import deepcopy
from math import pi
from unittest import TestCase

from shapely import wkt
from shapely.extension.geometry.arc import Arc
from shapely.geometry import Point, LineString, Polygon


class ArcTest(TestCase):
    def test_arc(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=90, angle_step=3)
        self.assertAlmostEqual(pi / 2, arc.length)
        self.assertTrue(arc.centroid.equals(Point(0, 0)))
        self.assertTrue(arc.is_ccw)
        self.assertTrue(arc.reverse.is_cw)
        self.assertEqual(90, arc.angle)
        self.assertTrue(arc.is_minor_arc)
        self.assertFalse(arc.is_prior_arc)
        self.assertFalse(arc.is_half_circle)
        self.assertTrue(arc.interpolate(0).equals(Point(1, 0)))

        copy_arc = deepcopy(arc)
        self.assertAlmostEqual(pi / 2, copy_arc.length)
        self.assertTrue(copy_arc.centroid.equals(Point(0, 0)))
        self.assertTrue(copy_arc.is_ccw)
        self.assertTrue(copy_arc.reverse.is_cw)
        self.assertEqual(90, copy_arc.angle)
        self.assertTrue(copy_arc.is_minor_arc)
        self.assertFalse(copy_arc.is_prior_arc)
        self.assertFalse(copy_arc.is_half_circle)
        self.assertTrue(copy_arc.interpolate(0).equals(Point(1, 0)))

    def test_complementary_arc(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=91, angle_step=3).complementary
        self.assertAlmostEqual((360 - 91) * pi / 180, arc.length)
        self.assertTrue(arc.centroid.equals(Point(0, 0)))
        self.assertFalse(arc.is_cw)
        self.assertEqual(360 - 91, arc.angle)
        self.assertFalse(arc.is_minor_arc)
        self.assertTrue(arc.is_prior_arc)
        self.assertFalse(arc.is_half_circle)

    def test_minor_arc_and_prior_arc(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=91, angle_step=3)
        complementary_arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=91, angle_step=3).complementary
        self.assertTrue(arc.get_minor_arc() is arc)
        self.assertTrue(complementary_arc.get_prior_arc() is complementary_arc)

        self.assertTrue(arc.get_prior_arc() == complementary_arc)
        self.assertAlmostEqual(complementary_arc.get_minor_arc().length, arc.length)

    def test_interpolate_by_angle(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=180)
        self.assertTrue(arc.interpolate_by_angle(90).almost_equals(Point(0, 1)))

    def test_tangential(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=180)
        self.assertTrue(arc.tangential(Point(0, 1)))
        self.assertFalse(arc.tangential(Point(0, 1.00001)))
        self.assertFalse(arc.tangential(Point(0, 0.99999)))
        self.assertFalse(arc.tangential(Point(0, -1)))

        self.assertTrue(arc.tangential(LineString([(-1, 1), (1, 1)])))
        self.assertFalse(arc.tangential(LineString([(-1, 0.9), (1, 1)])))
        self.assertFalse(arc.tangential(LineString([(-1, -1), (1, -1)])))

        self.assertTrue(arc.tangential(Polygon([(0, 1), (1, 1), (0, 2)])))
        self.assertFalse(arc.tangential(Polygon([(0, 0.9), (1, 1), (0, 2)])))
        self.assertFalse(arc.tangential(Polygon([(0, 1.1), (1, 1), (0, 2)])))
        self.assertFalse(arc.tangential(Polygon([(0, -1), (1, -1), (0, -2)])))

    def test_tangent_point(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=180)
        self.assertTrue(arc.tangent_point(Point(0, 1)).almost_equals(Point(0, 1)))
        self.assertTrue(arc.tangent_point(LineString([(-1, 1), (1, 1)])).almost_equals(Point(0, 1)))
        self.assertTrue(arc.tangent_point(Polygon([(0, 1), (1, 1), (0, 2)])).almost_equals(Point(0, 1)))

        self.assertFalse(arc.tangent_point(Polygon([(0, -1), (1, -1), (0, -2)])))
        self.assertFalse(arc.tangent_point(LineString([(-1, -1), (1, -1)])))
        self.assertFalse(arc.tangent_point(Point(0, -1)))

    def test_radius_line(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=180)
        self.assertTrue(arc.start_radius_line.almost_equals(LineString([(0, 0), (1, 0)])))
        self.assertTrue(arc.end_radius_line.almost_equals(LineString([(0, 0), (-1, 0)])))


class HalfArcTest(TestCase):
    def test_intersection_with_point(self):
        # 逆时针弧
        # 点在半弧上
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=180)
        result = arc.intersection(Point(0, 1))
        self.assertTrue(result.equals(Point(0, 1)))

        result = arc.intersection(Point(1, 0))
        self.assertTrue(result.equals(Point(1, 0)))

        # 点不在弧上
        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

        arc = Arc((0, 0), radius=5, start_angle=90, rotate_angle=180)
        result = arc.intersection(Point(0, 5))
        self.assertTrue(result.equals(Point(0, 5)))

        result = arc.intersection(Point(-5, 0))
        self.assertTrue(result.equals(Point(-5, 0)))

        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

        arc = Arc((0, 0), radius=5, start_angle=270, rotate_angle=180)
        result = arc.intersection(Point(0, 5))
        self.assertTrue(result.equals(Point(0, 5)))

        result = arc.intersection(Point(5, 0))
        self.assertTrue(result.equals(Point(5, 0)))

        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

        # 顺时针弧
        arc = Arc((0, 0), radius=5, start_angle=90, rotate_angle=-180)
        result = arc.intersection(Point(0, 5))
        self.assertTrue(result.equals(Point(0, 5)))

        result = arc.intersection(Point(5, 0))
        self.assertTrue(result.equals(Point(5, 0)))

        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

    def test_intersection_with_line(self):
        # 顺时针弧
        # 直线段和弧有一个交点
        arc = Arc((0, 0), radius=10, start_angle=0, rotate_angle=180)
        line = LineString([(0, 0), (0, 20)])
        result0 = arc._intersection_with_straight_segment(line)
        result1 = arc.intersection(line)
        self.assertTrue(result0.equals(result1))
        self.assertTrue(result0.equals(Point(0, 10)))

        # 弧和多段线有一个交点
        line2 = LineString([(0, 0), (0, 20), (20, 20)])
        with self.assertRaises(ValueError):
            arc._intersection_with_straight_segment(line2)
        result2 = arc.intersection(line2)
        self.assertTrue(result2.equals(Point(0, 10)))

        # 弧和多段线有两个交点
        line3 = LineString([(0, 0), (0, 20), (5, 20), (5, 0)])
        result3 = arc.intersection(line3)
        self.assertTrue(len(result3) == 2)
        self.assertTrue(result3.geoms[0].equals(Point(0, 10)))

        # 弧和直线无交点
        line4 = LineString([(0, 20), (20, 20)])
        result4 = arc.intersection(line4)
        result5 = arc._intersection_with_straight_segment(line4)
        self.assertTrue(result4.is_empty)
        self.assertTrue(result5.is_empty)

        # 弧和直线有两个交点
        line6 = LineString([(0.5, -0.5), (1.5, -1)])
        arc6 = Arc((0, 0), radius=1, start_angle=180, rotate_angle=180)
        result6 = arc6.intersection(line6)
        result7 = arc6._intersection_with_straight_segment(line6)
        self.assertAlmostEqual(result6.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result6.y, -0.635889894, delta=1e-6)
        self.assertAlmostEqual(result7.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result7.y, -0.635889894, delta=1e-6)

        # 弧和直线无交点
        line8 = LineString([(0, -20), (0, 0)])
        arc8 = Arc((0, 0), radius=1, start_angle=0, rotate_angle=180)
        result8 = arc8.intersection(line8)
        result9 = arc8._intersection_with_straight_segment(line8)
        self.assertTrue(result8.is_empty)
        self.assertTrue(result9.is_empty)

        # 顺时针弧
        line10 = LineString([(0, -20), (0, 0)])
        arc11 = Arc((0, 0), radius=1, start_angle=180, rotate_angle=-180)
        result10 = arc11.intersection(line10)
        result11 = arc11._intersection_with_straight_segment(line10)
        self.assertTrue(result10.is_empty)
        self.assertTrue(result11.is_empty)

        line13 = LineString([(0.5, -0.5), (1.5, -1)])
        arc13 = Arc((0, 0), radius=1, start_angle=0, rotate_angle=-180)
        result13 = arc13.intersection(line13)
        result14 = arc13._intersection_with_straight_segment(line13)
        self.assertAlmostEqual(result13.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result13.y, -0.635889894, delta=1e-6)
        self.assertAlmostEqual(result14.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result14.y, -0.635889894, delta=1e-6)

    def test_intersection_with_arc(self):
        # 逆时针弧
        # 有一个交点
        arc = Arc((0, 0), radius=1, start_angle=180, rotate_angle=180)
        arc0 = Arc((2, 0), radius=1, start_angle=180, rotate_angle=180)
        result = arc.intersection(arc0)
        result0 = arc._intersection_with_arc(arc0)
        self.assertTrue(result.equals(result0))
        self.assertTrue(result.equals(Point(1, 0)))

        arc1 = Arc((0, 0), radius=1, start_angle=270, rotate_angle=180)
        arc2 = Arc((2, 0), radius=1, start_angle=90, rotate_angle=180)
        result1 = arc1.intersection(arc2)
        result2 = arc1._intersection_with_arc(arc2)
        self.assertTrue(result1.equals(result2))
        self.assertTrue(result1.equals(Point(1, 0)))

        # 无交点
        arc3 = Arc((0, 0), radius=1, start_angle=270, rotate_angle=180)
        arc4 = Arc((3, 0), radius=1, start_angle=90, rotate_angle=180)
        result3 = arc3.intersection(arc4)
        result4 = arc3._intersection_with_arc(arc4)
        self.assertTrue(result3.equals(result4))
        self.assertTrue(result3.is_empty)

        # 有两个交点
        arc5 = Arc((0, 0), radius=1, start_angle=270, rotate_angle=180)
        arc6 = Arc((1.5, 0), radius=1, start_angle=90, rotate_angle=180)
        result5 = arc5.intersection(arc6)
        result6 = arc5._intersection_with_arc(arc6)
        self.assertTrue(result5.equals(result6))
        self.assertTrue(len(result5) == 2)

        # 有一个交点
        arc7 = Arc((0, 0), radius=10, start_angle=270, rotate_angle=180)
        arc8 = Arc((5, 0), radius=5, start_angle=270, rotate_angle=180)
        result7 = arc7.intersection(arc8)
        result8 = arc7._intersection_with_arc(arc8)
        self.assertTrue(result7.equals(result8))
        self.assertTrue(isinstance(result7, Point))
        self.assertTrue(result7.equals(Point(10, 0)))

        # 自相交
        result9 = arc7.intersection(arc7)
        self.assertTrue(isinstance(result9, LineString))

        # 两个交线
        arc10 = Arc((0, 0), radius=10, start_angle=0, rotate_angle=180)
        arc11 = Arc((0, 0), radius=10, start_angle=135, rotate_angle=270)
        result10 = arc10.intersection(arc11)
        result11 = arc10._intersection_with_arc(arc11)
        self.assertTrue(result10.equals(result11))
        self.assertTrue(len(result10) == 2)

        # 两个交点
        arc12 = Arc((0, 0), radius=10, start_angle=0, rotate_angle=180)
        arc13 = Arc((0, 0), radius=10, start_angle=180, rotate_angle=180)
        result12 = arc12.intersection(arc13)
        result13 = arc12._intersection_with_arc(arc13)
        self.assertTrue(result12.equals(result13))
        self.assertTrue(len(result10) == 2)

        # 顺时针弧
        # 一个交点
        arc14 = Arc((0, 0), radius=1, start_angle=180, rotate_angle=-180)
        arc15 = Arc((2, 0), radius=1, start_angle=180, rotate_angle=-180)
        result14 = arc14.intersection(arc15)
        result15 = arc14._intersection_with_arc(arc15)
        self.assertTrue(result14.equals(result15))
        self.assertTrue(result.equals(Point(1, 0)))

        # 一个交点
        arc16 = Arc((0, 0), radius=1, start_angle=90, rotate_angle=-180)
        arc17 = Arc((2, 0), radius=1, start_angle=270, rotate_angle=-180)
        result16 = arc16.intersection(arc17)
        result17 = arc16._intersection_with_arc(arc17)
        self.assertTrue(result16.equals(result17))
        self.assertTrue(result16.equals(Point(1, 0)))

        # 两个交线
        arc18 = Arc((0, 0), radius=10, start_angle=180, rotate_angle=-180)
        arc19 = Arc((0, 0), radius=10, start_angle=45, rotate_angle=-270)
        result18 = arc18.intersection(arc19)
        result19 = arc18._intersection_with_arc(arc19)
        self.assertTrue(result18.equals(result19))
        self.assertTrue(len(result18) == 2)

        # 自相交
        result20 = arc18.intersection(arc18)
        self.assertTrue(isinstance(result20, LineString))

    def test_arc_buffer(self):
        empty_polygon = wkt.loads("POLYGON EMPTY")
        arc = Arc((0, 0), radius=1, start_angle=270, rotate_angle=180)
        result = arc.buffer(0)
        self.assertTrue(empty_polygon.equals(result))

        result0 = arc.buffer(0, single_sided=True)
        self.assertTrue(empty_polygon.equals(result0))

        result1 = arc.buffer(0.5)
        expect1 = Polygon(list(Arc((0, 0), radius=1.5, start_angle=270, rotate_angle=180).coords) +
                          list(reversed(Arc((0, 0), radius=0.5, start_angle=270, rotate_angle=180).coords)))
        self.assertTrue(result1.equals(expect1))

        result2 = arc.buffer(0.5, single_sided=True)
        expect2 = Polygon(list(Arc((0, 0), radius=1.5, start_angle=270, rotate_angle=180).coords) +
                          list(reversed(Arc((0, 0), radius=1, start_angle=270, rotate_angle=180).coords)))
        self.assertTrue(result2.equals(expect2))

        result3 = arc.buffer(1)
        expect3 = Polygon(list(Arc((0, 0), radius=2, start_angle=270, rotate_angle=180).coords) + [(0, 0)])
        self.assertTrue(result3.equals(expect3))

        result4 = arc.buffer(1, single_sided=True)
        expect4 = Polygon(list(Arc((0, 0), radius=2, start_angle=270, rotate_angle=180).coords) +
                          list(reversed(Arc((0, 0), radius=1, start_angle=270, rotate_angle=180).coords)))
        self.assertTrue(result4.equals(expect4))

        result5 = arc.buffer(-0.5)
        expect5 = Polygon(list(Arc((0, 0), radius=0.5, start_angle=270, rotate_angle=180).coords) +
                          list(reversed(Arc((0, 0), radius=1.5, start_angle=270, rotate_angle=180).coords)))
        self.assertTrue(result5.equals(expect5))

        result6 = arc.buffer(-0.5, single_sided=True)
        expect6 = Polygon(list(Arc((0, 0), radius=1, start_angle=270, rotate_angle=180).coords) +
                          list(reversed(Arc((0, 0), radius=0.5, start_angle=270, rotate_angle=180).coords)))
        self.assertTrue(result6.equals(expect6))

        result7 = arc.buffer(-1)
        expect7 = Polygon(list(Arc((0, 0), radius=2, start_angle=270, rotate_angle=180).coords) + [(0, 0)])
        self.assertTrue(result7.equals(expect7))

        result8 = arc.buffer(-1, single_sided=True)
        expect8 = Polygon(list(Arc((0, 0), radius=1, start_angle=270, rotate_angle=180).coords) + [(0, 0)])
        self.assertTrue(result8.equals(expect8))


class PriorArcTest(TestCase):
    def test_intersection_with_point(self):
        # 逆时针弧
        # 点在半弧上
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=225)
        result = arc.intersection(Point(0, 1))
        self.assertTrue(result.equals(Point(0, 1)))

        result = arc.intersection(Point(1, 0))
        self.assertTrue(result.equals(Point(1, 0)))

        # 点不在弧上
        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

        arc = Arc((0, 0), radius=5, start_angle=90, rotate_angle=225)
        result = arc.intersection(Point(0, 5))
        self.assertTrue(result.equals(Point(0, 5)))

        result = arc.intersection(Point(-5, 0))
        self.assertTrue(result.equals(Point(-5, 0)))

        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

        arc = Arc((0, 0), radius=5, start_angle=270, rotate_angle=225)
        result = arc.intersection(Point(0, 5))
        self.assertTrue(result.equals(Point(0, 5)))

        result = arc.intersection(Point(5, 0))
        self.assertTrue(result.equals(Point(5, 0)))

        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

        # 顺时针弧
        arc = Arc((0, 0), radius=5, start_angle=90, rotate_angle=-225)
        result = arc.intersection(Point(0, 5))
        self.assertTrue(result.equals(Point(0, 5)))

        result = arc.intersection(Point(5, 0))
        self.assertTrue(result.equals(Point(5, 0)))

        result = arc.intersection(Point(0, -1))
        self.assertTrue(result.is_empty)

    def test_intersection_with_line(self):
        # 顺时针弧
        # 直线段和弧有一个交点
        arc = Arc((0, 0), radius=10, start_angle=0, rotate_angle=225)
        line = LineString([(0, 0), (0, 20)])
        result0 = arc._intersection_with_straight_segment(line)
        result1 = arc.intersection(line)
        self.assertTrue(result0.equals(result1))
        self.assertTrue(result0.equals(Point(0, 10)))

        # 弧和多段线有一个交点
        line2 = LineString([(0, 0), (0, 20), (20, 20)])
        with self.assertRaises(ValueError):
            arc._intersection_with_straight_segment(line2)
        result2 = arc.intersection(line2)
        self.assertTrue(result2.equals(Point(0, 10)))

        # 弧和多段线有两个交点
        line3 = LineString([(0, 0), (0, 20), (5, 20), (5, 0)])
        result3 = arc.intersection(line3)
        self.assertTrue(len(result3) == 2)
        self.assertTrue(result3.geoms[0].equals(Point(0, 10)))

        # 弧和直线无交点
        line4 = LineString([(0, 20), (20, 20)])
        result4 = arc.intersection(line4)
        result5 = arc._intersection_with_straight_segment(line4)
        self.assertTrue(result4.is_empty)
        self.assertTrue(result5.is_empty)

        # 弧和直线有两个交点
        line6 = LineString([(0.5, -0.5), (1.5, -1)])
        arc6 = Arc((0, 0), radius=1, start_angle=180, rotate_angle=225)
        result6 = arc6.intersection(line6)
        result7 = arc6._intersection_with_straight_segment(line6)
        self.assertAlmostEqual(result6.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result6.y, -0.635889894, delta=1e-6)
        self.assertAlmostEqual(result7.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result7.y, -0.635889894, delta=1e-6)

        # 弧和直线无交点
        line8 = LineString([(0, -20), (0, 0)])
        arc8 = Arc((0, 0), radius=1, start_angle=0, rotate_angle=225)
        result8 = arc8.intersection(line8)
        result9 = arc8._intersection_with_straight_segment(line8)
        self.assertTrue(result8.is_empty)
        self.assertTrue(result9.is_empty)

        # 顺时针弧
        line10 = LineString([(0, -20), (0, 0)])
        arc11 = Arc((0, 0), radius=1, start_angle=180, rotate_angle=-225)
        result10 = arc11.intersection(line10)
        result11 = arc11._intersection_with_straight_segment(line10)
        self.assertTrue(result10.is_empty)
        self.assertTrue(result11.is_empty)

        line13 = LineString([(0.5, -0.5), (1.5, -1)])
        arc13 = Arc((0, 0), radius=1, start_angle=0, rotate_angle=-225)
        result13 = arc13.intersection(line13)
        result14 = arc13._intersection_with_straight_segment(line13)
        self.assertAlmostEqual(result13.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result13.y, -0.635889894, delta=1e-6)
        self.assertAlmostEqual(result14.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result14.y, -0.635889894, delta=1e-6)

    def test_intersection_with_arc(self):
        # 逆时针弧
        # 有一个交点
        arc = Arc((0, 0), radius=1, start_angle=180, rotate_angle=225)
        arc0 = Arc((2, 0), radius=1, start_angle=180, rotate_angle=180)
        result = arc.intersection(arc0)
        result0 = arc._intersection_with_arc(arc0)
        self.assertTrue(result.equals(result0))
        self.assertTrue(result.equals(Point(1, 0)))

        arc1 = Arc((0, 0), radius=1, start_angle=270, rotate_angle=225)
        arc2 = Arc((2, 0), radius=1, start_angle=90, rotate_angle=180)
        result1 = arc1.intersection(arc2)
        result2 = arc1._intersection_with_arc(arc2)
        self.assertTrue(result1.equals(result2))
        self.assertTrue(result1.equals(Point(1, 0)))

        # 无交点
        arc3 = Arc((0, 0), radius=1, start_angle=270, rotate_angle=225)
        arc4 = Arc((3, 0), radius=1, start_angle=90, rotate_angle=180)
        result3 = arc3.intersection(arc4)
        result4 = arc3._intersection_with_arc(arc4)
        self.assertTrue(result3.equals(result4))
        self.assertTrue(result3.is_empty)

        # 有两个交点
        arc5 = Arc((0, 0), radius=1, start_angle=270, rotate_angle=225)
        arc6 = Arc((1.5, 0), radius=1, start_angle=90, rotate_angle=180)
        result5 = arc5.intersection(arc6)
        result6 = arc5._intersection_with_arc(arc6)
        self.assertTrue(result5.equals(result6))
        self.assertTrue(len(result5) == 2)

        # 有一个交点
        arc7 = Arc((0, 0), radius=10, start_angle=270, rotate_angle=225)
        arc8 = Arc((5, 0), radius=5, start_angle=270, rotate_angle=180)
        result7 = arc7.intersection(arc8)
        result8 = arc7._intersection_with_arc(arc8)
        self.assertTrue(result7.equals(result8))
        self.assertTrue(isinstance(result7, Point))
        self.assertTrue(result7.equals(Point(10, 0)))

        # 自相交
        result9 = arc7.intersection(arc7)
        self.assertTrue(isinstance(result9, LineString))

        # 两个交线
        arc10 = Arc((0, 0), radius=10, start_angle=0, rotate_angle=225)
        arc11 = Arc((0, 0), radius=10, start_angle=135, rotate_angle=270)
        result10 = arc10.intersection(arc11)
        result11 = arc10._intersection_with_arc(arc11)
        self.assertTrue(result10.equals(result11))
        self.assertTrue(len(result10) == 2)

        # 两个交点
        arc12 = Arc((0, 0), radius=10, start_angle=0, rotate_angle=225)
        arc13 = Arc((0, 0), radius=10, start_angle=180, rotate_angle=180)
        result12 = arc12.intersection(arc13)
        result13 = arc12._intersection_with_arc(arc13)
        self.assertTrue(result12.equals(result13))
        self.assertTrue(len(result10) == 2)

        # 顺时针弧
        # 一个交点
        arc14 = Arc((0, 0), radius=1, start_angle=180, rotate_angle=-225)
        arc15 = Arc((2, 0), radius=1, start_angle=180, rotate_angle=-180)
        result14 = arc14.intersection(arc15)
        result15 = arc14._intersection_with_arc(arc15)
        self.assertTrue(result14.equals(result15))
        self.assertTrue(result.equals(Point(1, 0)))

        # 一个交点
        arc16 = Arc((0, 0), radius=1, start_angle=90, rotate_angle=-225)
        arc17 = Arc((2, 0), radius=1, start_angle=270, rotate_angle=-180)
        result16 = arc16.intersection(arc17)
        result17 = arc16._intersection_with_arc(arc17)
        self.assertTrue(result16.equals(result17))
        self.assertTrue(result16.equals(Point(1, 0)))

        # 两个交线
        arc18 = Arc((0, 0), radius=10, start_angle=180, rotate_angle=-225)
        arc19 = Arc((0, 0), radius=10, start_angle=45, rotate_angle=-270)
        result18 = arc18.intersection(arc19)
        result19 = arc18._intersection_with_arc(arc19)
        self.assertTrue(result18.equals(result19))
        self.assertTrue(len(result18) == 2)

        # 自相交
        result20 = arc18.intersection(arc18)
        self.assertTrue(isinstance(result20, LineString))

    def test_arc_buffer(self):
        empty_polygon = wkt.loads("POLYGON EMPTY")
        arc = Arc((0, 0), radius=1, start_angle=225, rotate_angle=225)
        result = arc.buffer(0)
        self.assertTrue(empty_polygon.equals(result))

        result0 = arc.buffer(0, single_sided=True)
        self.assertTrue(empty_polygon.equals(result0))

        result1 = arc.buffer(0.5)
        expect1 = Polygon(list(Arc((0, 0), radius=1.5, start_angle=225, rotate_angle=225).coords) +
                          list(reversed(Arc((0, 0), radius=0.5, start_angle=225, rotate_angle=225).coords)))
        self.assertTrue(result1.equals(expect1))

        result2 = arc.buffer(0.5, single_sided=True)
        expect2 = Polygon(list(Arc((0, 0), radius=1.5, start_angle=225, rotate_angle=225).coords) +
                          list(reversed(Arc((0, 0), radius=1, start_angle=225, rotate_angle=225).coords)))
        self.assertTrue(result2.equals(expect2))

        result3 = arc.buffer(1)
        expect3 = Polygon(list(Arc((0, 0), radius=2, start_angle=225, rotate_angle=225).coords) + [(0, 0)])
        self.assertTrue(result3.equals(expect3))

        result4 = arc.buffer(1, single_sided=True)
        expect4 = Polygon(list(Arc((0, 0), radius=2, start_angle=225, rotate_angle=225).coords) +
                          list(reversed(Arc((0, 0), radius=1, start_angle=225, rotate_angle=225).coords)))
        self.assertTrue(result4.equals(expect4))

        result5 = arc.buffer(-0.5)
        expect5 = Polygon(list(Arc((0, 0), radius=0.5, start_angle=225, rotate_angle=225).coords) +
                          list(reversed(Arc((0, 0), radius=1.5, start_angle=225, rotate_angle=225).coords)))
        self.assertTrue(result5.equals(expect5))

        result6 = arc.buffer(-0.5, single_sided=True)
        expect6 = Polygon(list(Arc((0, 0), radius=1, start_angle=225, rotate_angle=225).coords) +
                          list(reversed(Arc((0, 0), radius=0.5, start_angle=225, rotate_angle=225).coords)))
        self.assertTrue(result6.equals(expect6))

        result7 = arc.buffer(-1)
        expect7 = Polygon(list(Arc((0, 0), radius=2, start_angle=225, rotate_angle=225).coords) + [(0, 0)])
        self.assertTrue(result7.equals(expect7))

        result8 = arc.buffer(-1, single_sided=True)
        expect8 = Polygon(list(Arc((0, 0), radius=1, start_angle=225, rotate_angle=225).coords) + [(0, 0)])
        self.assertTrue(result8.equals(expect8))


class MinorArcTest(TestCase):
    def test_intersection_with_point(self):
        arc = Arc((0, 0), radius=1, start_angle=0, rotate_angle=30)
        result = arc.intersection(Point(1, 0))
        self.assertTrue(result.equals(Point(1, 0)))

        result1 = arc.intersection(Point(2, 0))
        self.assertTrue(result1.is_empty)

        arc2 = Arc((0, 0), radius=1, start_angle=30, rotate_angle=-30)
        result2 = arc2.intersection(Point(1, 0))
        self.assertTrue(result2.equals(Point(1, 0)))

        result3 = arc2.intersection(Point(0, 0))
        self.assertTrue(result3.is_empty)

    def test_intersection_with_line(self):
        # 顺时针弧
        # 直线段和弧有一个交点
        arc = Arc((0, 0), radius=10, start_angle=60, rotate_angle=60)
        line = LineString([(0, 0), (0, 20)])
        result0 = arc._intersection_with_straight_segment(line)
        result1 = arc.intersection(line)
        self.assertTrue(result0.equals(result1))
        self.assertTrue(result0.equals(Point(0, 10)))

        # 弧和多段线有一个交点
        line2 = LineString([(0, 0), (0, 20), (20, 20)])
        with self.assertRaises(ValueError):
            arc._intersection_with_straight_segment(line2)
        result2 = arc.intersection(line2)
        self.assertTrue(result2.equals(Point(0, 10)))

        # 弧和多段线有两个交点
        line3 = LineString([(0, 0), (0, 20), (2, 20), (2, 0)])
        result3 = arc.intersection(line3)
        self.assertTrue(len(result3) == 2)
        self.assertTrue(result3.geoms[0].equals(Point(0, 10)))

        # 弧和直线无交点
        line4 = LineString([(0, 20), (20, 20)])
        result4 = arc.intersection(line4)
        result5 = arc._intersection_with_straight_segment(line4)
        self.assertTrue(result4.is_empty)
        self.assertTrue(result5.is_empty)

        # 弧和直线有两个交点
        line6 = LineString([(0.5, -0.5), (1.5, -1)])
        arc6 = Arc((0, 0), radius=1, start_angle=300, rotate_angle=50)
        result6 = arc6.intersection(line6)
        result7 = arc6._intersection_with_straight_segment(line6)
        self.assertAlmostEqual(result6.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result6.y, -0.635889894, delta=1e-6)
        self.assertAlmostEqual(result7.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result7.y, -0.635889894, delta=1e-6)

        # 弧和直线无交点
        line8 = LineString([(0, -20), (0, 0)])
        arc8 = Arc((0, 0), radius=1, start_angle=0, rotate_angle=30)
        result8 = arc8.intersection(line8)
        result9 = arc8._intersection_with_straight_segment(line8)
        self.assertTrue(result8.is_empty)
        self.assertTrue(result9.is_empty)

        # 顺时针弧
        line10 = LineString([(0, -20), (0, 0)])
        arc11 = Arc((0, 0), radius=1, start_angle=120, rotate_angle=-60)
        result10 = arc11.intersection(line10)
        result11 = arc11._intersection_with_straight_segment(line10)
        self.assertTrue(result10.is_empty)
        self.assertTrue(result11.is_empty)

        line13 = LineString([(0.5, -0.5), (1.5, -1)])
        arc13 = Arc((0, 0), radius=1, start_angle=350, rotate_angle=-50)
        result13 = arc13.intersection(line13)
        result14 = arc13._intersection_with_straight_segment(line13)
        self.assertAlmostEqual(result13.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result13.y, -0.635889894, delta=1e-6)
        self.assertAlmostEqual(result14.x, 0.771779788, delta=1e-6)
        self.assertAlmostEqual(result14.y, -0.635889894, delta=1e-6)

    def test_intersection_with_arc(self):
        # 逆时针弧
        # 有一个交点
        arc = Arc((0, 0), radius=1, start_angle=350, rotate_angle=50)
        arc0 = Arc((2, 0), radius=1, start_angle=180, rotate_angle=180)
        result = arc.intersection(arc0)
        result0 = arc._intersection_with_arc(arc0)
        self.assertTrue(result.equals(result0))
        self.assertTrue(result.equals(Point(1, 0)))

    def test_arc_buffer(self):
        empty_polygon = wkt.loads("POLYGON EMPTY")
        arc = Arc((0, 0), radius=1, start_angle=345, rotate_angle=30)
        result = arc.buffer(0)
        self.assertTrue(result.equals(empty_polygon))

        result0 = arc.buffer(0, single_sided=True)
        self.assertTrue(empty_polygon.equals(result0))

        result1 = arc.buffer(0.5)
        expect1 = Polygon(list(Arc((0, 0), radius=1.5, start_angle=345, rotate_angle=30).coords) +
                          list(reversed(Arc((0, 0), radius=0.5, start_angle=345, rotate_angle=30).coords)))
        self.assertTrue(result1.equals(expect1))

        result2 = arc.buffer(0.5, single_sided=True)
        expect2 = Polygon(list(Arc((0, 0), radius=1.5, start_angle=345, rotate_angle=30).coords) +
                          list(reversed(Arc((0, 0), radius=1, start_angle=345, rotate_angle=30).coords)))
        self.assertTrue(result2.equals(expect2))

        result3 = arc.buffer(1)
        expect3 = Polygon(list(Arc((0, 0), radius=2, start_angle=345, rotate_angle=30).coords) + [(0, 0)])
        self.assertTrue(result3.equals(expect3))

        result4 = arc.buffer(1, single_sided=True)
        expect4 = Polygon(list(Arc((0, 0), radius=2, start_angle=345, rotate_angle=30).coords) +
                          list(reversed(Arc((0, 0), radius=1, start_angle=345, rotate_angle=30).coords)))
        self.assertTrue(result4.equals(expect4))

        result5 = arc.buffer(-0.5)
        expect5 = Polygon(list(Arc((0, 0), radius=0.5, start_angle=345, rotate_angle=30).coords) +
                          list(reversed(Arc((0, 0), radius=1.5, start_angle=345, rotate_angle=30).coords)))
        self.assertTrue(result5.equals(expect5))

        result6 = arc.buffer(-0.5, single_sided=True)
        expect6 = Polygon(list(Arc((0, 0), radius=1, start_angle=345, rotate_angle=30).coords) +
                          list(reversed(Arc((0, 0), radius=0.5, start_angle=345, rotate_angle=30).coords)))
        self.assertTrue(result6.equals(expect6))

        result7 = arc.buffer(-1)
        expect7 = Polygon(list(Arc((0, 0), radius=2, start_angle=345, rotate_angle=30).coords) + [(0, 0)])
        self.assertTrue(result7.equals(expect7))

        result8 = arc.buffer(-1, single_sided=True)
        expect8 = Polygon(list(Arc((0, 0), radius=1, start_angle=345, rotate_angle=30).coords) + [(0, 0)])
        self.assertTrue(result8.equals(expect8))
