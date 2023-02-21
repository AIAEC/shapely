from operator import attrgetter
from unittest import TestCase

from shapely.extension.constant import MATH_EPS
from shapely.extension.model.envelope import Envelope, PointPosition, EdgePosition, HalfEdgePosition, DiagonalPosition, \
    HalfDiagonalPosition, EnvelopeCreator
from shapely.geometry import Point, Polygon, LineString, box
from shapely.wkt import loads


class EnvelopeTest(TestCase):
    def test_create_envelope_by_point(self):
        envelope = Envelope(Point(0, 0))
        self.assertTrue(isinstance(envelope.shape, Polygon))
        self.assertEqual(0, envelope.angle)
        for position in PointPosition.enums():
            self.assertTrue(envelope.point(position).equals(Point(0, 0)))

        for position in PointPosition.enums():
            self.assertTupleEqual((0, 0), envelope.coord(position))

        for position in EdgePosition.enums():
            self.assertEqual(0, envelope.edge(position).length)

        for position in HalfEdgePosition.enums():
            self.assertEqual(0, envelope.half_edge(position).length)

        for position in DiagonalPosition.enums():
            self.assertEqual(0, envelope.diagonal(position).length)

        for position in HalfDiagonalPosition.enums():
            self.assertEqual(0, envelope.half_diagonal(position).length)

        self.assertEqual(0, envelope.longer_length)
        self.assertEqual(0, envelope.shorter_length)
        self.assertEqual(float('inf'), envelope.aspect_ratio)
        self.assertEqual(0, envelope.longer_edges[0].length)
        self.assertEqual(0, envelope.longer_edges[1].length)
        self.assertEqual(0, envelope.shorter_edges[0].length)
        self.assertEqual(0, envelope.shorter_edges[1].length)
        self.assertEqual(0, envelope.shorter_edges[0].length)
        self.assertEqual(0, envelope.shorter_edges[1].length)
        self.assertEqual(0, envelope.longer_mid_line.length)
        self.assertEqual(0, envelope.shorter_mid_line.length)
        self.assertEqual(0, envelope.width)
        self.assertEqual(0, envelope.depth)
        self.assertEqual(4, len(envelope.edges))
        self.assertEqual(0, envelope.edges[0].length)
        self.assertEqual(0, envelope.edges[1].length)
        self.assertEqual(0, envelope.edges[2].length)
        self.assertEqual(0, envelope.edges[3].length)

    def test_create_envelope_by_points(self):
        points = [Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)]
        envelope = Envelope(points)
        self.assertTrue(isinstance(envelope.shape, Polygon))
        self.assertTrue(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]).equals(envelope.shape))
        self.assertEqual(0, envelope.angle)
        self.assertTupleEqual((0, 0), envelope.coord(PointPosition.LEFT_BOTTOM))
        self.assertTupleEqual((0.5, 0), envelope.coord(PointPosition.MID_BOTTOM))
        self.assertTupleEqual((1, 0), envelope.coord(PointPosition.RIGHT_BOTTOM))
        self.assertTupleEqual((0, 0.5), envelope.coord(PointPosition.LEFT_HORIZON))
        self.assertTupleEqual((0.5, 0.5), envelope.coord(PointPosition.MID_HORIZON))
        self.assertTupleEqual((1, 0.5), envelope.coord(PointPosition.RIGHT_HORIZON))
        self.assertTupleEqual((0, 1), envelope.coord(PointPosition.LEFT_TOP))
        self.assertTupleEqual((0.5, 1), envelope.coord(PointPosition.MID_TOP))
        self.assertTupleEqual((1, 1), envelope.coord(PointPosition.RIGHT_TOP))
        self.assertEqual(1, envelope.width)
        self.assertEqual(1, envelope.depth)

    def test_create_envelope_by_points1(self):
        points = [Point(0.5, 0), Point(1, 0.5), Point(0.5, 1), Point(0, 0.3)]
        envelope = Envelope(points, angle=0)
        self.assertTrue(isinstance(envelope.shape, Polygon))
        self.assertTrue(Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]).equals(envelope.shape))
        self.assertEqual(0, envelope.angle)
        self.assertTupleEqual((0, 0), envelope.coord(PointPosition.LEFT_BOTTOM))
        self.assertTupleEqual((0.5, 0), envelope.coord(PointPosition.MID_BOTTOM))
        self.assertTupleEqual((1, 0), envelope.coord(PointPosition.RIGHT_BOTTOM))
        self.assertTupleEqual((0, 0.5), envelope.coord(PointPosition.LEFT_HORIZON))
        self.assertTupleEqual((0.5, 0.5), envelope.coord(PointPosition.MID_HORIZON))
        self.assertTupleEqual((1, 0.5), envelope.coord(PointPosition.RIGHT_HORIZON))
        self.assertTupleEqual((0, 1), envelope.coord(PointPosition.LEFT_TOP))
        self.assertTupleEqual((0.5, 1), envelope.coord(PointPosition.MID_TOP))
        self.assertTupleEqual((1, 1), envelope.coord(PointPosition.RIGHT_TOP))
        self.assertEqual(1, envelope.width)
        self.assertEqual(1, envelope.depth)

    def test_create_envelope_by_points2(self):
        """
        原图形和envelope中心不同时
        """
        multi_points = loads(
            'MULTIPOINT (-16.367780269621388 4.1313879604772, -14.918891530187786 3.743159392823419, -14.840605022568914 6.933106095671379)')
        envelope = Envelope(multi_points)
        self.assertTrue(envelope.shape.buffer(MATH_EPS).contains(multi_points))


def test_geoms():
    p = Point(1, 0)
    envelope = Envelope(geom_or_geoms=p)
    assert [p] == envelope.geoms

    pts = [Point(0, 0), p]
    envelope = Envelope(geom_or_geoms=pts)
    assert pts == envelope.geoms


class EnvelopeCreatorTest(TestCase):
    def test_create_by_angle(self):
        line = LineString([(0, 0), (1, 1)])
        envelope = EnvelopeCreator(line).of_angle(0)
        self.assertTrue(envelope.point(PointPosition.LEFT_BOTTOM).equals(Point(0, 0)))
        self.assertTrue(envelope.point(PointPosition.RIGHT_BOTTOM).equals(Point(1, 0)))
        self.assertTrue(envelope.point(PointPosition.RIGHT_TOP).equals(Point(1, 1)))
        self.assertTrue(envelope.point(PointPosition.LEFT_TOP).equals(Point(0, 1)))
        self.assertEqual(1, envelope.width)
        self.assertEqual(1, envelope.depth)

        envelope1 = EnvelopeCreator(line).of_angle()
        self.assertTrue(envelope1.point(PointPosition.LEFT_BOTTOM).equals(Point(0, 0)))
        self.assertTrue(envelope1.point(PointPosition.RIGHT_BOTTOM).equals(Point(1, 0)))
        self.assertTrue(envelope1.point(PointPosition.RIGHT_TOP).equals(Point(1, 1)))
        self.assertTrue(envelope1.point(PointPosition.LEFT_TOP).equals(Point(0, 1)))
        self.assertEqual(1, envelope.width)
        self.assertEqual(1, envelope.depth)

    def test_create_tighten(self):
        line = LineString([(0, 0), (1, 1)])
        envelope = EnvelopeCreator(line).tightened()
        self.assertTrue(envelope.point(PointPosition.LEFT_BOTTOM).almost_equals(Point(0, 0)))

        poly = Polygon([(0, 0), (1, 1), (0, 2), (-1, 1)])
        envelope = EnvelopeCreator(poly).tightened()
        self.assertTrue(envelope.shape.almost_equals(poly))
        self.assertAlmostEqual(1.4, envelope.width, delta=0.2)
        self.assertAlmostEqual(1.4, envelope.depth, delta=0.2)

    def test_create_by_geometry_obj(self):
        from dataclasses import dataclass
        @dataclass
        class Test:
            geom: Polygon

        case = Test(Polygon([(0, 2), (2, 0), (3, 1), (1, 3)]))
        envelope = EnvelopeCreator(case, attr_getter=attrgetter('geom')).tightened()
        self.assertEqual(135, envelope.angle)

    def test_min_envelope(self):
        case = loads(
            'MULTIPOLYGON (((1235293.565547209 412609.2938603121, 1236093.565547209 412609.2938603121, 1236093.565547209 411809.2938603122, 1235293.565547209 411809.2938603122, 1235293.565547209 412609.2938603121)), ((1235293.565547248 433809.2938603008, 1235293.565547248 439409.2938353083, 1236093.565547295 439409.2938353083, 1236093.565547295 433809.2938603008, 1235293.565547248 433809.2938603008)))')
        envelope = EnvelopeCreator(case).of_angle(90)
        target_obj = loads(
            'POLYGON ((1236093.565547295 411809.2938603124, 1236093.565547295 439409.2938353083, 1235293.565547209 439409.2938353083, 1235293.565547209 411809.2938603124, 1236093.565547295 411809.2938603124))')
        self.assertTrue(envelope.shape.almost_equals(target_obj))

    def test_envelope_top_edge(self):
        rectangle = Polygon([(0, 0), (1, 0), (1, 3), (0, 3)])
        envelope = EnvelopeCreator(rectangle).of_angle(90)
        self.assertTrue(LineString([envelope.left_top, envelope.right_top]).equals(envelope.edge(EdgePosition.TOP)))
        self.assertEqual(3, envelope.width)
        self.assertEqual(1, envelope.depth)

        shorter_edges = envelope.shorter_edges
        self.assertAlmostEqual(shorter_edges[0].ext.angle().degree, shorter_edges[1].ext.reverse().ext.angle().degree)

        longer_edges = envelope.longer_edges
        self.assertAlmostEqual(longer_edges[0].ext.angle().degree, longer_edges[1].ext.reverse().ext.angle().degree)


def test_edge_direction():
    envelope = Envelope(box(0, 0, 1, 1), angle=0)
    assert LineString([(0, 0), (0, 1)]) == envelope.edge(EdgePosition.LEFT)
    assert LineString([(1, 0), (1, 1)]) == envelope.edge(EdgePosition.RIGHT)

    assert LineString([(0, 0), (1, 0)]) == envelope.edge(EdgePosition.BOTTOM)
    assert LineString([(0, 1), (1, 1)]) == envelope.edge(EdgePosition.TOP)
