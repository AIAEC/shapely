import math
from collections import deque
from operator import attrgetter
from unittest import TestCase

from shapely.extension.model.vector import Vector
from shapely.geometry import box, Point, LineString, GeometryCollection
from shapely.geometry.base import BaseGeometry

MATH_EPS = 1e-6
MATH_LARGE_EPS = 1e-3


class TestVector(TestCase):
    def test_is_valid_2d_coordinate(self):
        self.assertTrue(Vector._is_coord((0, 1)))
        self.assertTrue(Vector._is_coord((0., 1)))
        self.assertFalse(Vector._is_coord((0., 1, 2)))
        self.assertFalse(Vector._is_coord((0., 1, '2')))
        self.assertFalse(Vector._is_coord(0))
        self.assertFalse(Vector._is_coord([9]))
        self.assertFalse(Vector._is_coord(['a']))
        self.assertFalse(Vector._is_coord(['a', 1]))

    def test_from_tuple(self):
        vector1 = Vector.from_tuple([0, 1])
        self.assertTrue(isinstance(vector1, Vector))
        self.assertEqual(0, vector1.x)
        self.assertEqual(1, vector1.y)

        vector2 = Vector.from_tuple((1, 2))
        self.assertTrue(isinstance(vector2, Vector))
        self.assertEqual(1, vector2.x)
        self.assertEqual(2, vector2.y)

        with self.assertRaises(ValueError):
            Vector.from_tuple([1])
        with self.assertRaises(ValueError):
            Vector.from_tuple(['a', 1, 1])

    def test_from_point(self):
        vector1 = Vector.from_point(Point(0, 0))
        self.assertEqual(0, vector1.length)

        vector2 = Vector.from_point(Point(1, 1))
        self.assertEqual(Vector(1, 1), vector2)

    def test_from_coordinates(self):
        vector1 = Vector.from_origin_to_target((0, 0), (1, 1))
        self.assertTrue(isinstance(vector1, Vector))
        self.assertEqual(1, vector1.x)
        self.assertEqual(1, vector1.y)

        with self.assertRaises(ValueError):
            Vector.from_origin_to_target(('a', 1), [1, 1])
        with self.assertRaises(ValueError):
            Vector.from_origin_to_target((0, 1), [1])

    def test_from_points(self):
        from_point = Point(0, 0)
        to_point = Point(1, 1)
        vector = Vector.from_origin_to_target(from_point, to_point)
        self.assertTrue(isinstance(vector, Vector))
        self.assertEqual(1, vector.x)
        self.assertEqual(1, vector.y)

    def test_len(self):
        vector1 = Vector(1, 0)
        self.assertAlmostEqual(1.0, vector1.length)

        vector2 = Vector(2, 0)
        self.assertAlmostEqual(2.0, vector2.length)

        vector3 = Vector(1, 1)
        self.assertAlmostEqual(2 ** 0.5, vector3.length)

    def test_dot(self):
        vector1 = Vector(1, 1)
        vector2 = Vector(-1, -1)
        self.assertAlmostEqual(-2, vector1.dot(vector2), delta=0)
        self.assertAlmostEqual(-2, vector2.dot(vector1), delta=0)
        self.assertAlmostEqual(-2, vector1 @ vector2, delta=0)

        vector3 = Vector(1, 1)
        vector4 = Vector(-1, 1)
        self.assertEqual(0, vector3.dot(vector4))
        self.assertEqual(0, vector4.dot(vector1))
        self.assertEqual(0, vector3 @ vector4)

    @staticmethod
    def _is_geom_equal(geom1: BaseGeometry, geom2: BaseGeometry):
        return geom1.symmetric_difference(geom2).area < MATH_EPS

    def test_apply_to_simple_geom(self):
        polygon = box(0, 0, 1, 1)
        vector = Vector(1, 1)
        expected = box(1, 1, 2, 2)
        self.assertTrue(self._is_geom_equal(expected, vector.apply(polygon)))

        vector = Vector(1, 0)
        geom_col = GeometryCollection([box(0, 0, 1, 1), Point(1, 1), LineString([(0, 0), (1, 1)])])
        expected = GeometryCollection([box(1, 0, 2, 1), Point(2, 1), LineString([(1, 0), (2, 1)])])
        self.assertTrue(self._is_geom_equal(expected, vector.apply(geom_col)))

    def test_apply_to_geom_iterable(self):
        vector = Vector(1, 1)
        geom_list = [box(0, 0, 1, 1), box(1, 1, 2, 2)]
        moved_geom_list = vector.apply(geom_list)
        self.assertEqual(2, len(moved_geom_list))
        self._is_geom_equal(box(1, 1, 2, 2), moved_geom_list[0])
        self._is_geom_equal(box(2, 2, 3, 3), moved_geom_list[1])

        geom_deque = deque([box(0, 0, 1, 1), box(1, 1, 2, 2)])
        moved_geom_deque = vector.apply(geom_deque)
        self.assertEqual(2, len(moved_geom_deque))
        self._is_geom_equal(box(1, 1, 2, 2), moved_geom_deque[0])
        self._is_geom_equal(box(2, 2, 3, 3), moved_geom_deque[1])

        geom_tuple = tuple([box(0, 0, 1, 1), box(1, 1, 2, 2)])
        moved_geom_tuple = vector.apply(geom_tuple)
        self.assertEqual(2, len(moved_geom_tuple))
        self._is_geom_equal(box(1, 1, 2, 2), moved_geom_tuple[0])
        self._is_geom_equal(box(2, 2, 3, 3), moved_geom_tuple[1])

    def test_apply_to_geom_obj(self):
        class Test:
            def __init__(self):
                self.geom = box(0, 0, 1, 1)
                self.other = 1

            @property
            def geom_property(self):
                return Point(0, 0)

        case0 = Test()
        vector = Vector(1, 1)
        result = vector.apply(case0, attrgetter('geom'))
        self.assertTrue(isinstance(result, Test))
        self._is_geom_equal(box(1, 1, 2, 2), result.geom)

        result = vector.apply(case0, attrgetter('geom_property'))
        self.assertTrue(isinstance(result, Test))
        self._is_geom_equal(box(1, 1, 2, 2), result.geom)

    def test_apply_to_geom_obj_without_attrgetter(self):
        class Test:
            def __init__(self):
                self.geom = box(0, 0, 1, 1)
                self.other = 1

        vector = Vector(1, 1)
        with self.assertRaises(ValueError):
            vector.apply(Test())

    def test_plus(self):
        vector1 = Vector(1, 3.14)
        vector2 = Vector(-1, -2)
        expected = Vector(0, 1.14)

        def _assert_vector_almost_equal(vector0, vector1):
            for val0, val1 in zip(vector0, vector1):
                self.assertAlmostEqual(val0, val1)

        _assert_vector_almost_equal(expected, vector1.plus(vector2))
        _assert_vector_almost_equal(expected, vector2.plus(vector1))
        _assert_vector_almost_equal(expected, vector1 + vector2)
        _assert_vector_almost_equal(expected, vector2 + vector1)

        self.assertEqual(1, vector1.x)
        self.assertEqual(3.14, vector1.y)
        self.assertEqual(-1, vector2.x)
        self.assertEqual(-2, vector2.y)

    def test_eq(self):
        vector1 = Vector(1, 3.14)
        vector2 = Vector(-1, -2)
        vector3 = Vector(1, 3.14)

        self.assertEqual(vector1, vector3)
        self.assertNotEqual(vector1, vector2)

    def test_almost_equal(self):
        vector1 = Vector(3.14, 10.18)
        vector2 = vector1.unit(vector1.length)
        self.assertTrue(vector1.almost_equal(vector2))

    def test_bool(self):
        vector0 = Vector(0, 0)
        self.assertFalse(vector0)

        vector1 = Vector(1, 0)
        self.assertTrue(vector1)

    def test_vector_multiply(self):
        vector = Vector(1, 1)
        vector1 = vector.multiply(10)
        self.assertEqual(Vector(10, 10), vector1)

        vector2 = vector * 3
        self.assertEqual(Vector(3, 3), vector2)

        vector3 = 3 * vector
        self.assertEqual(Vector(3, 3), vector3)

        vector *= 3
        self.assertEqual(Vector(3, 3), vector)

    def test_vector_div(self):
        vector = Vector(3, 3)
        self.assertEqual(Vector(1, 1), vector / 3)

    def test_get_unit_vector(self):
        vector1 = Vector(2, 2)
        vector2 = Vector(1, 1)
        self.assertEqual(vector1.unit(), vector2.unit())
        self.assertFalse(vector1 is vector1.unit())

        vector3 = Vector(2, 0)
        self.assertEqual(Vector(1, 0), vector3.unit())

    def test_reverse(self):
        vector1 = Vector(2, 1)
        reversed_vec = vector1.invert()
        self.assertEqual(Vector(-2, -1), reversed_vec)

    def test_angle(self):
        vector1 = Vector(1, 1)
        self.assertAlmostEqual(45, vector1.angle.degree)

        vector2 = Vector(-1, 1)
        self.assertAlmostEqual(135, vector2.angle.degree)

        vector3 = Vector(-1, -1)
        self.assertAlmostEqual(225, vector3.angle.degree)

        vector4 = Vector(1, -1)
        self.assertAlmostEqual(315, vector4.angle.degree)

    def test_ray(self):
        origin = (0, 0)
        vector = Vector(0, -1)
        line = vector.ray(origin)
        self.assertEqual(1e9, line.length)
        self.assertEqual(LineString([(0, 0), (0, -1e9)]), line)

    def test_from_angle(self):
        vector = Vector.from_angle()
        self.assertEqual(Vector.from_origin_to_target((1, 0), (2, 0)), vector)

        vector = Vector.from_angle(angle_degree=-45, length=100 * math.sqrt(2))
        self.assertAlmostEqual(100, vector.x)
        self.assertAlmostEqual(-100, vector.y)

    def test_from_endpoints_of_linestring(self):
        line = LineString([(0, 0), (1, 0), (1, 1)])
        vec = Vector.from_endpoints_of(line)
        self.assertAlmostEqual(Vector(1, 1), vec)

    def test_hash(self):
        s = set()
        s.add(Vector(1, 0))
        s.add(Vector(1, 0))
        s.add(Vector(1, 0))
        self.assertEqual(1, len(s))

    def test_rotate(self):
        v = Vector(1, 0)
        rotated_v = v.rotate(90)
        self.assertAlmostEqual(rotated_v, Vector(0, 1))

    def test_perpendicular_to(self):
        vector0 = Vector(0, 1)
        vector1 = Vector(1, 0)
        self.assertTrue(vector0.perpendicular_to(vector1))

        vector2 = Vector(1, 1e-6)
        self.assertTrue(vector0.perpendicular_to(vector2, dist_tol=1e-3))

        vector3 = Vector(-1, -1e-6)
        self.assertTrue(vector0.perpendicular_to(vector3, dist_tol=1e-3))

        vector4 = Vector(0.5, 0.5)
        self.assertTrue(vector4.perpendicular_to(vector0, angle_tol=46))
        self.assertFalse(vector4.perpendicular_to(vector0, angle_tol=44))

    def test_parallel_to(self):
        vector0 = Vector(0, 1)
        vector1 = Vector(0, -10)
        self.assertTrue(vector0.parallel_to(vector1))

        vector2 = Vector(-0.0001, -10)
        self.assertTrue(vector0.parallel_to(vector2, dist_tol=1e-2))

        vector3 = Vector(1, 1)
        vector4 = Vector(-0.001, -0.001001)
        self.assertTrue(vector3.parallel_to(vector4, dist_tol=1e-3))

        vector5 = Vector(1, -1)
        self.assertTrue(vector5.parallel_to(vector0, angle_tol=46))
        self.assertFalse(vector5.parallel_to(vector0, angle_tol=44))

    def test_sub_vector(self):
        vector0 = Vector(1, 1)
        direction0 = Vector(1, 0)
        result = vector0.sub_vector(direction0)
        self.assertEqual(Vector(1, 0), result)

        direction1= Vector(0, 1)
        result = vector0.sub_vector(direction1)
        self.assertEqual(Vector(0, 1), result)

        direction2 = Vector(-1, 0)
        result = vector0.sub_vector(direction2)
        self.assertEqual(Vector(1, 0), result)

        vector1 = Vector(2, 0)
        result = vector1.sub_vector(Vector(10, 10))
        self.assertAlmostEqual(1, result.x)
        self.assertAlmostEqual(1, result.y)
