from unittest import TestCase

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
