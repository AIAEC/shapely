from unittest import TestCase

from shapely.geometry import Point, Polygon, box, LineString


class BufferTest(TestCase):
    def test_rect_buffer_point(self):
        point = Point(0, 0)
        result = point.ext.buffer().rect(1)
        self.assertTrue(isinstance(result, Polygon))
        self.assertTrue(result.equals(box(-0.5, -0.5, 0.5, 0.5)))

    def test_rect_buffer_other(self):
        poly = box(0, 0, 1, 1)
        result = poly.ext.buffer().rect(1)
        self.assertTrue(result.equals(box(-1, -1, 2, 2)))

    def test_single_sided_rect_buffer(self):
        line = LineString([(0, 0), (1, 0)])
        result = line.ext.buffer().single_sided().rect(1)
        self.assertTrue(result.equals(box(0, 0, 1, 1)))

    def test_round_buffer(self):
        point = Point(0, 0)
        result = point.ext.buffer().round(1)
        self.assertTrue(result.equals(point.buffer(1)))
