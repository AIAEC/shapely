from itertools import combinations
from math import radians, pi, sin, cos, tan, isclose
from unittest import TestCase

from shapely.extension.model.angle import Angle


class AngleTest(TestCase):
    def test_init_guard(self):
        # positive case
        try:
            Angle(1)
            Angle(2, range_=(-90, 90))
            Angle(3, range_=(-90, 270))
        except:
            self.fail()

        # negative case
        with self.assertRaises(TypeError):
            Angle('a')

        with self.assertRaises(ValueError):
            Angle(1, 'a')

        with self.assertRaises(ValueError):
            Angle(1, [1, 2, 3])

        with self.assertRaises(ValueError):
            Angle(1, [1, 1])

    def test_mod_degree_in_given_range(self):
        """ test whether the output angle degree in range """

        def assert_valid_degree_mod(origin_angle, range_, expect_angle):
            angle = Angle(origin_angle, range_)
            self.assertEqual(expect_angle, angle.degree)

        # range is (0, 90)
        assert_valid_degree_mod(origin_angle=0, range_=(0, 90), expect_angle=0)
        assert_valid_degree_mod(origin_angle=89.99, range_=(0, 90), expect_angle=89.99)
        assert_valid_degree_mod(origin_angle=90, range_=(0, 90), expect_angle=90)
        assert_valid_degree_mod(origin_angle=120, range_=(0, 90), expect_angle=30)

        # range is (-90, 90)
        assert_valid_degree_mod(origin_angle=-100, range_=(-90, 90), expect_angle=80)
        assert_valid_degree_mod(origin_angle=-90, range_=(-90, 90), expect_angle=-90)
        assert_valid_degree_mod(origin_angle=-0, range_=(-90, 90), expect_angle=0)
        assert_valid_degree_mod(origin_angle=90, range_=(-90, 90), expect_angle=90)
        assert_valid_degree_mod(origin_angle=120, range_=(-90, 90), expect_angle=-60)

        # range is (-90, 270)
        assert_valid_degree_mod(origin_angle=-100, range_=(-90, 270), expect_angle=260)
        assert_valid_degree_mod(origin_angle=-90, range_=(-90, 270), expect_angle=-90)
        assert_valid_degree_mod(origin_angle=-0, range_=(-90, 270), expect_angle=0)
        assert_valid_degree_mod(origin_angle=270, range_=(-90, 270), expect_angle=270)
        assert_valid_degree_mod(origin_angle=280, range_=(-90, 270), expect_angle=-80)

        # range is (-5, 5)
        assert_valid_degree_mod(origin_angle=-21, range_=(-5, 5), expect_angle=-1)
        assert_valid_degree_mod(origin_angle=-5, range_=(-5, 5), expect_angle=-5)
        assert_valid_degree_mod(origin_angle=-0, range_=(-5, 5), expect_angle=-0)
        assert_valid_degree_mod(origin_angle=5, range_=(-5, 5), expect_angle=5)
        assert_valid_degree_mod(origin_angle=13, range_=(-5, 5), expect_angle=3)

        # range is (0, 720)
        assert_valid_degree_mod(origin_angle=-1, range_=(0, 720), expect_angle=719)
        assert_valid_degree_mod(origin_angle=0, range_=(0, 720), expect_angle=0)
        assert_valid_degree_mod(origin_angle=719, range_=(0, 720), expect_angle=719)
        assert_valid_degree_mod(origin_angle=720, range_=(0, 720), expect_angle=720)
        assert_valid_degree_mod(origin_angle=721, range_=(0, 720), expect_angle=1)

        # range is in negative side, (-180, 0)
        assert_valid_degree_mod(origin_angle=-181, range_=(-180, 0), expect_angle=-1)
        assert_valid_degree_mod(origin_angle=-180, range_=(-180, 0), expect_angle=-180)
        assert_valid_degree_mod(origin_angle=-90, range_=(-180, 0), expect_angle=-90)
        assert_valid_degree_mod(origin_angle=-0, range_=(-180, 0), expect_angle=0)

    def test_radian(self):
        self.assertAlmostEqual(radians(1), Angle(1, (0, 180)).radian)
        self.assertAlmostEqual(pi, Angle(180, (0, 180)).radian)
        self.assertAlmostEqual(Angle(1, (0, 360)).radian, Angle(361, (0, 360)).radian)

    def test_mod_related_methods(self):
        # test default mod space
        angle = Angle(1)
        self.assertTupleEqual((0, 360), angle.mod)

        # test specified mod space
        angle = Angle(1, (-90, 90))
        self.assertTupleEqual((-90, 90), angle.mod)

        # test set mod
        angle = Angle(1, (-90, 90))
        angle.mod = (-180, 0)
        self.assertTupleEqual((-180, 0), angle.mod)

        angle = Angle(1, (-90, 90))
        angle.set_mod((-180, 0))
        self.assertTupleEqual((-180, 0), angle.mod)

        angle = Angle(1, (-90, 90))
        angle %= (-180, 0)
        self.assertTupleEqual((-180, 0), angle.mod)

        angle = Angle(1, (-90, 90))
        angle = angle[-180: 0]
        self.assertTupleEqual((-180, 0), angle.mod)

    def test_float(self):
        angle = Angle(1.1)
        self.assertEqual(1.1, float(angle))

        angle = Angle(-1, (0, 90))
        self.assertEqual(-1, float(angle))
        self.assertNotEqual(angle.degree, float(angle))

    def test_int(self):
        angle = Angle(1.1)
        self.assertEqual(1, int(angle))

        angle = Angle(181.1, (0, 90))
        self.assertEqual(181, int(angle))

    def test_trigonometric(self):
        angle = Angle(45)
        self.assertAlmostEqual(sin(pi / 4), angle.sin())
        self.assertAlmostEqual(cos(pi / 4), angle.cos())
        self.assertAlmostEqual(tan(pi / 4), angle.tan())

        self.assertAlmostEqual(90, Angle.atan2(1, 0))
        self.assertAlmostEqual(45, Angle.atan(1))
        self.assertAlmostEqual(30, Angle.asin(0.5).degree)
        self.assertAlmostEqual(60, Angle.acos(0.5).degree)

    def test_math_operator(self):
        angle = Angle(45)
        self.assertEqual(90, angle + 45)
        self.assertEqual(0, angle - 45)
        self.assertEqual(90, angle * 2)
        self.assertEqual(9, angle / 5)

        self.assertEqual(90, angle + Angle(45, (0, 720)))
        self.assertEqual(0, angle - Angle(45, (0, 720)))

        angle.almost_equal(45.1, angle_tol=0.2)

        self.assertTrue(0 < angle < Angle(46))

    def test_rotating_to(self):
        angle = Angle(4, (0, 180))
        self.assertEqual(86, angle.rotating_angle(90, direct='ccw'))
        self.assertEqual(94, angle.rotating_angle(90, direct='cw'))

        angle = Angle(-1, (0, 360))
        self.assertEqual(2, angle.rotating_angle(1, direct='ccw'))
        self.assertEqual(358, angle.rotating_angle(1, direct='cw'))
        self.assertEqual(179, angle.rotating_angle(180, direct='cw'))

        angle = Angle(90, (-90, 90))
        self.assertEqual(0, angle.rotating_angle(90))

        # here we calculate including angle to be 180, but in modulo space of (-90, 90), the
        # degree here will be 90
        self.assertEqual(90, angle.rotating_angle(-90, direct='cw').degree)
        self.assertEqual(180, float(angle.rotating_angle(-90, direct='cw')))

    def test_including_angle(self):
        angle = Angle(4, (0, 180))
        self.assertEqual(8, angle.including_angle(-4))
        self.assertEqual(8, angle.including_angle(Angle(-4, (0, 180))))

        angle = Angle(40, (0, 360))
        self.assertEqual(90, angle.including_angle(-50))

    def test_is_close(self):
        angle0 = Angle(0)
        angle1 = Angle(0.001)
        angle2 = Angle(-0.001)
        self.assertTrue(isclose(angle0, angle1, abs_tol=0.1))
        self.assertTrue(isclose(angle0, angle2, abs_tol=0.1))
        self.assertTrue(isclose(angle1, angle2, abs_tol=0.1))
        self.assertFalse(isclose(angle0, 180, abs_tol=0.1))
        self.assertFalse(isclose(angle0, 179.99, abs_tol=0.1))

    def test_almost_equal(self):
        angle0 = Angle(0)
        angle1 = Angle(0.001)
        angle2 = Angle(-0.001)
        for a0, a1 in combinations([angle0, angle1, angle2], 2):
            self.assertTrue(a0.almost_equal(a1, angle_tol=0.1))

        self.assertTrue(angle1.almost_equal(-0.001, angle_tol=0.1))
        self.assertTrue((angle1 % 180).almost_equal(179.999, angle_tol=0.1))
        self.assertTrue((angle1 % 360).almost_equal(359.999, angle_tol=0.1))

    def test_bool(self):
        self.assertTrue(Angle(1))
        self.assertFalse(Angle(float('nan')))
        self.assertFalse(Angle.atan2(0, 0))

    def test_complementary(self):
        angle = Angle(180) % 180
        self.assertEqual(0, angle.complementary())

        angle = Angle(0) % 180
        self.assertEqual(180, angle.complementary())

        angle = Angle(0)
        self.assertEqual(360, angle.complementary())

    def test_parallel_to(self):
        angle = Angle(181)
        self.assertTrue(angle.parallel_to(Angle(1)))
        self.assertTrue(angle.parallel_to(Angle(361)))
        self.assertTrue(angle.parallel_to(Angle(361.5), angle_tol=2))

    def test_perpendicular_to(self):
        angle = Angle(181)
        self.assertTrue(angle.perpendicular_to(91))
        self.assertTrue(angle.perpendicular_to(271))
        self.assertTrue(angle.perpendicular_to(271.5, angle_tol=2))
