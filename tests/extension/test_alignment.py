from _operator import attrgetter
from math import sqrt
from unittest import TestCase

from shapely.extension.model.alignment import AlignPoint, AlignLineString, AlignPolygon
from shapely.extension.model.vector import Vector
from shapely.geometry import Point, LineString, box, Polygon


class AlignObjectTest(TestCase):
    def test_distance_between_points(self):
        point0 = AlignPoint(Point(0, 0), direction=Vector(0, 1))
        point1 = AlignPoint(Point(1, 0), direction=Vector(0, 1))
        dist = point0.distance(point1)
        self.assertEqual(1, dist)
        dist = point1.distance(point0)
        self.assertEqual(1, dist)

        point2 = AlignPoint(Point(0, 0), direction=Vector(1, 1))
        point3 = AlignPoint(Point(1, 0), direction=Vector(1, 1))
        dist = point2.distance(point3)
        self.assertAlmostEqual(1 / sqrt(2), dist)
        dist = point3.distance(point2)
        self.assertAlmostEqual(1 / sqrt(2), dist)

        point4 = AlignPoint(Point(1, 0), direction=Vector(-1, -1))
        dist = point2.distance(point4)
        self.assertAlmostEqual(1 / sqrt(2), dist)

    def test_distance_between_lines(self):
        line0 = AlignLineString(LineString([(0, 0), (10, 0)]))
        line1 = AlignLineString(LineString([(12, 5), (22, 5)]))
        self.assertEqual(5, line0.distance(line1))
        self.assertEqual(5, line1.distance(line0))

        line2 = AlignLineString(LineString([(0, 0), (1, 1)]))
        line3 = AlignLineString(LineString([(10, 0), (11, 1)]))
        self.assertAlmostEqual(10 / sqrt(2), line2.distance(line3))
        self.assertAlmostEqual(10 / sqrt(2), line3.distance(line2))

        line4 = AlignLineString(LineString([(10, 1), (11, 1)]))
        with self.assertRaises(ValueError):
            line2.distance(line4)
        with self.assertRaises(ValueError):
            line4.distance(line2)

    def test_distance_between_line_and_point(self):
        point0 = AlignPoint(Point(0, 0), direction=Vector(0, 1))
        line0 = AlignLineString(LineString([(10, 0), (10, 10)]))
        self.assertAlmostEqual(10, point0.distance(line0))
        self.assertAlmostEqual(10, line0.distance(point0))

        line1 = AlignLineString(LineString([(12, 5), (22, 5)]))
        with self.assertRaises(ValueError):
            line1.distance(line0)
        with self.assertRaises(ValueError):
            line0.distance(line1)

        point1 = AlignPoint(Point(0, 0), direction=Vector(1, 0))
        self.assertAlmostEqual(5, point1.distance(line1))
        self.assertAlmostEqual(5, line1.distance(point1))

    def test_distance_between_poly_and_line(self):
        poly = AlignPolygon(box(0, 0, 1, 1))
        line0 = AlignLineString(LineString([(0, -1), (1, -1)]))
        result = poly.distances_to(line0)
        self.assertEqual(2, len(result))
        result.sort()
        self.assertAlmostEqual(1, result[0])
        self.assertAlmostEqual(2, result[1])

        result = poly.distances_from(line0)
        self.assertEqual(2, len(result))
        result.sort()
        self.assertAlmostEqual(1, result[0])
        self.assertAlmostEqual(2, result[1])

        line1 = AlignLineString(LineString([(100, 0.3), (101, 0.3)]))
        result = poly.distances_to(line1)
        self.assertEqual(2, len(result))
        result.sort()
        self.assertAlmostEqual(0.3, result[0])
        self.assertAlmostEqual(0.7, result[1])

        line1 = AlignLineString(LineString([(100, 0.3), (101, 0.3)]))
        result = poly.distances_from(line1)
        self.assertEqual(2, len(result))
        result.sort()
        self.assertAlmostEqual(0.3, result[0])
        self.assertAlmostEqual(0.7, result[1])

    def test_distance_between_poly_and_point(self):
        poly = AlignPolygon(box(0, 0, 1, 1))
        point = AlignPoint(Point(2, 2), direction=Vector(1, 1))
        self.assertListEqual([], poly.distances_to(point))

        point = AlignPoint(Point(2, 2), direction=Vector(0, 1))
        result = poly.distances_to(point)
        self.assertEqual(2, len(result))
        result.sort()
        self.assertAlmostEqual(1, result[0])
        self.assertAlmostEqual(2, result[1])

    def test_distance_between_polys(self):
        poly0 = AlignPolygon(box(0, 0, 1, 1))
        poly1 = AlignPolygon(box(2, 2, 3, 3))
        result = poly0.distances_to(poly1)
        self.assertEqual(8, len(result))

        poly3 = AlignPolygon(box(0, 0, 1, 1), direction=Vector(1, 1))
        result = poly1.distances_to(poly3)
        self.assertEqual(0, len(result))

        poly4 = AlignPolygon(box(0, 0, 1, 1), direction=Vector(0, 1), angle_tol=1e-6)
        poly5 = AlignPolygon(box(3, 3, 4, 4), direction=Vector(0, 1))
        result = poly4.distances_to(poly5)
        self.assertEqual(4, len(result))
        result.sort()
        self.assertAlmostEqual(2, result[0])
        self.assertAlmostEqual(3, result[1])
        self.assertAlmostEqual(3, result[2])
        self.assertAlmostEqual(4, result[3])

    def test_vector_of_points(self):
        point0 = AlignPoint(Point(0, 0), direction=Vector(0, 1))
        point1 = AlignPoint(Point(1, 0), direction=Vector(0, 1))
        vec = point0.vector_to(point1)
        self.assertEqual(Vector(1, 0), vec)

        vec = point1.vector_to(point0)
        self.assertEqual(Vector(-1, 0), vec)

        point2 = AlignPoint(Point(0, 0), direction=Vector(1, 1))
        point3 = AlignPoint(Point(1, 0), direction=Vector(1, 1))
        vec = point2.vector_to(point3)
        self.assertTrue(vec.almost_equal(Vector(0.5, -0.5)))

        vec = point3.vector_to(point2)
        self.assertTrue(vec.almost_equal(Vector(-0.5, 0.5)))

    def test_vector_of_lines(self):
        line0 = AlignLineString(LineString([(1, 1), (2, 2)]))
        line1 = AlignLineString(LineString([(0, 0), (10, 10)]))
        vec = line0.vector_to(line1)
        self.assertAlmostEqual(0, vec.length)

        line2 = AlignLineString(LineString([(3, 0), (6, 3)]))
        vec = line0.vector_to(line2)
        self.assertTrue(Vector(1.5, -1.5).almost_equal(vec))

        vec = line2.vector_to(line0)
        self.assertTrue(Vector(-1.5, 1.5).almost_equal(vec))

    def test_vector_of_point_and_line(self):
        line0 = AlignLineString(LineString([(1, 1), (2, 2)]))
        point0 = AlignPoint(Point(0, 0), direction=Vector(-1, -1))
        self.assertAlmostEqual(0, line0.vector_to(point0).length)

        point1 = AlignPoint(Point(-1, 0), direction=Vector(-1, -1))
        self.assertTrue(line0.vector_to(point1).almost_equal(Vector(-0.5, 0.5)))

    def test_vector_of_poly_and_line(self):
        poly = AlignPolygon(box(0, 0, 1, 1))
        line = AlignLineString(LineString([(10, 0), (10, 11)]))
        vecs = poly.vectors_to(line)
        self.assertEqual(2, len(vecs))
        vecs.sort(key=attrgetter('length'))
        self.assertTrue(vecs[0].almost_equal(Vector(9, 0)))
        self.assertTrue(vecs[1].almost_equal(Vector(10, 0)))

        vecs = poly.vectors_from(line)
        vecs.sort(key=attrgetter('length'))
        self.assertTrue(vecs[0].almost_equal(Vector(-9, 0)))
        self.assertTrue(vecs[1].almost_equal(Vector(-10, 0)))

    def test_vector_of_polys(self):
        poly0 = AlignPolygon(box(0, 0, 1, 1), direction=Vector(1, 0))
        poly1 = AlignPolygon(box(0, 1, 1, 2))
        vecs = poly0.vectors_to(poly1)
        self.assertEqual(4, len(vecs))
        vecs.sort(key=attrgetter('length'))
        self.assertTrue(vecs[0].almost_equal(Vector.zero()))
        self.assertTrue(vecs[1].almost_equal(Vector(0, 1)))
        self.assertTrue(vecs[2].almost_equal(Vector(0, 1)))
        self.assertTrue(vecs[3].almost_equal(Vector(0, 2)))

    def test_direct_check_between_points(self):
        point0 = AlignPoint(Point(0, 0), direction=Vector(1, 0))
        point1 = AlignPoint(Point(0, 0), direction=Vector(0, 1))
        with self.assertRaises(ValueError):
            point0.assert_align_item_matched(point1)

    def test_align_point_alignable(self):
        point0 = AlignPoint(Point(0, 0), direction=Vector(1, 0), angle_tol=10)
        point1 = AlignPoint(Point(0, 1), direction=Vector(1, 0.1))
        self.assertTrue(point0.alignable_to(point1))
        self.assertFalse(point1.alignable_to(point0))

        point2 = AlignPoint(Point(0, 2), direction=Vector(1, 0.1), direction_dist_tol=0.1)
        self.assertTrue(point2.alignable_to(point0))

        point3 = AlignPoint(Point(0, 3), direction=Vector(1, 0.1), direction_dist_tol=0, angle_tol=0)
        self.assertFalse(point3.alignable_to(point0))

    def test_align_line_alignable(self):
        line = AlignLineString(LineString([(0, 0), (1, 0)]), angle_tol=1)
        point = AlignPoint(Point(0, 0), direction=Vector(1, 0.01), angle_tol=0, direction_dist_tol=0)
        self.assertTrue(line.alignable_to(point))
        self.assertFalse(point.alignable_to(line))

    def test_align_poly_alignable(self):
        poly = AlignPolygon(Polygon([(0, 0), (1, 1), (0, 2), (-1, 1)]), angle_tol=1)
        line = AlignLineString(LineString([(0, 0), (1, 1.01)]), direction_dist_tol=0, angle_tol=0)
        self.assertTrue(poly.alignable_to(line))
