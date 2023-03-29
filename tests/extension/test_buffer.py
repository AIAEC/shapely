from unittest import TestCase

from shapely import wkt
from shapely.extension.geometry.arc import Arc
from shapely.extension.geometry.circle import Circle
from shapely.geometry import Point, Polygon, box, LineString


class BufferTest(TestCase):
    def test_rect_buffer_point(self):
        point = Point(0, 0)
        result = point.ext.buffer().rect(1)
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.equals(box(-0.5, -0.5, 0.5, 0.5)))

        result2 = point.ext.buffer().rect(-2)
        self.assertTrue(isinstance(result2, Polygon))
        self.assertTrue(result2.is_empty)

    def test_rect_buffer_other(self):
        poly = box(0, 0, 1, 1)
        result = poly.ext.buffer().rect(1)
        self.assertTrue(result.equals(box(-1, -1, 2, 2)))

        poly2 = box(0, 0, 2, 2)
        result2 = poly2.ext.buffer().rect(-0.5)
        self.assertTrue(result2.equals(box(0.5, 0.5, 1.5, 1.5)))

    def test_single_sided_rect_buffer(self):
        line = LineString([(0, 0), (1, 0)])
        result = line.ext.buffer().single_sided().rect(1)
        self.assertTrue(result.equals(box(0, 0, 1, 1)))

        line2 = LineString([(0, 0), (1, 0)])
        result2 = line2.ext.buffer().single_sided().rect(-1)
        self.assertTrue(result2.equals(box(0, 0, 1, -1)))

    def test_round_buffer(self):
        point = Point(0, 0)
        result = point.ext.buffer().round(1)
        self.assertTrue(result.equals(point.buffer(1)))

        result2 = point.ext.buffer().round(-1)
        self.assertTrue(result2.is_empty)

    def test_single_sided_round_buffer(self):
        point = Point(0, 0)
        result = point.ext.buffer().single_sided().round(1)
        self.assertTrue(result.equals(point.buffer(1, single_sided=True)))

        result2 = point.ext.buffer().single_sided().round(-1)
        self.assertTrue(result2.is_empty)

    def test_circle_buffer(self):
        empty_polygon = wkt.loads("POLYGON EMPTY")
        circle = Circle(center=Point(0, 0), radius=10, angle_step=16)
        result = circle.ext.buffer().rect(5)
        expect = Polygon(Circle(center=Point(0, 0), radius=15, angle_step=16),
                         [list(reversed(Circle(center=Point(0, 0), radius=5, angle_step=16).coords))])
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.equals(expect))
        self.assertEqual(len(result.interiors), 1)

        result = circle.ext.buffer().rect(10)
        expect = Polygon(Circle(center=Point(0, 0), radius=20, angle_step=16))
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.equals(expect))
        self.assertEqual(len(result.interiors), 0)

        result = circle.ext.buffer().rect(30)
        expect = Polygon(Circle(center=Point(0, 0), radius=40, angle_step=16))
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.equals(expect))
        self.assertEqual(len(result.interiors), 0)

        result = circle.ext.buffer().rect(0)
        self.assertTrue(result.equals(empty_polygon))

    def test_arc_buffer(self):
        arc = Arc(center=Point(0, 0), radius=10, start_angle=10, rotate_angle=90, angle_step=16)
        result = arc.ext.buffer().rect(5)
        expect = Polygon(
            list(Arc(center=Point(0, 0), radius=15, start_angle=10, rotate_angle=90, angle_step=16).coords)
            + list(reversed(Arc(center=Point(0, 0), radius=5, start_angle=10, rotate_angle=90, angle_step=16).coords)))
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.almost_equals(expect))
        self.assertEqual(len(result.interiors), 0)

        result = arc.ext.buffer().rect(10)
        expect = Polygon(
            list(Arc(center=Point(0, 0), radius=20, start_angle=10, rotate_angle=90, angle_step=16).coords) + [(0, 0)])
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.almost_equals(expect))
        self.assertEqual(len(result.interiors), 0)

        result = arc.ext.buffer().rect(30)
        expect = Polygon(
            list(Arc(center=Point(0, 0), radius=40, start_angle=10, rotate_angle=90, angle_step=16).coords) + [(0, 0)])
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.almost_equals(expect))
        self.assertEqual(len(result.interiors), 0)
