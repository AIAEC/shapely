from unittest import TestCase

from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.vector import Vector
from shapely.extension.util.arrow_creator import FixHeadArrowFactory, FixRatioArrowFactory
from shapely.geometry import Point, LineString


class FixHeadStrategyTest(TestCase):
    def test_origin_and_vector(self):
        strategy = FixHeadArrowFactory(1, 2, 1)
        vector = Vector(1, 0)
        result = strategy.from_origin_and_vector(Point(0, 0), vector, 2)
        self.assertTrue(result.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result.is_closed)
        self.assertTrue(len(result.coords) == 3)
        self.assertTrue(len(result.arrow_direction()) == 1)
        self.assertTrue(result.arrow_direction()[0].almost_equal(vector))
        
        result1 = strategy.from_origin_and_vector(Point(0, 0), vector, 2, True)
        self.assertTrue(result1.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result1.is_closed)
        self.assertTrue(len(result1.coords) == 3)
        self.assertTrue(len(result1.arrow_direction()) == 1)
        self.assertTrue(result1.arrow_direction()[0].invert().almost_equal(vector))

    def test_straight_line(self):
        strategy = FixHeadArrowFactory(1, 2, 1)
        vector = Vector(1, 0)
        straight_line = StraightSegment([(0, 0), (2, 0)])
        result2 = strategy.from_straight_line(straight_line)
        self.assertTrue(result2.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result2.is_closed)
        self.assertTrue(len(result2.coords) == 3)
        self.assertTrue(len(result2.arrow_direction()) == 1)
        self.assertTrue(result2.arrow_direction()[0].almost_equal(vector))

        result3 = strategy.from_straight_line(straight_line, True)
        self.assertTrue(result3.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result3.is_closed)
        self.assertTrue(len(result3.coords) == 3)
        self.assertTrue(len(result3.arrow_direction()) == 1)
        self.assertTrue(result3.arrow_direction()[0].invert().almost_equal(vector))

    def test_line(self):
        strategy = FixHeadArrowFactory(1, 2, 1)
        vector = Vector(1, 0)
        line = LineString([(0, 0), (2, 0)])
        result4 = strategy.from_straight_line(line)
        self.assertTrue(result4.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result4.is_closed)
        self.assertTrue(len(result4.coords) == 3)
        self.assertTrue(len(result4.arrow_direction()) == 1)
        self.assertTrue(result4.arrow_direction()[0].almost_equal(vector))

        result5 = strategy.from_straight_line(line, True)
        self.assertTrue(result5.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result5.is_closed)
        self.assertTrue(len(result5.coords) == 3)
        self.assertTrue(len(result5.arrow_direction()) == 1)
        self.assertTrue(result5.arrow_direction()[0].invert().almost_equal(vector))

        line1 = LineString([(0, 0), (1, 0), (2, 0)])
        result6 = strategy.from_straight_line(line1)
        self.assertTrue(result6.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result6.is_closed)
        self.assertTrue(len(result6.coords) == 3)
        self.assertTrue(len(result6.arrow_direction()) == 1)
        self.assertTrue(result6.arrow_direction()[0].almost_equal(vector))
    
        result7 = strategy.from_straight_line(line1, True)
        self.assertTrue(result7.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result7.is_closed)
        self.assertTrue(len(result7.coords) == 3)
        self.assertTrue(len(result7.arrow_direction()) == 1)
        self.assertTrue(result7.arrow_direction()[0].invert().almost_equal(vector))

    def test_polygonal_Line(self):
        strategy = FixHeadArrowFactory(1, 2, 1)
        vector = Vector(1, 0)
        line = LineString([(0, -1), (1, 0), (2, 0), (3, 0)])
        result8 = strategy.from_line(line)
        print(result8.shape)
        self.assertTrue(result8.axis.equals(LineString([(0, -1), (1, 0), (2, 0), (3, 0)])))
        self.assertFalse(result8.is_closed)
        self.assertTrue(len(result8.coords) == 4)
        self.assertTrue(len(result8.arrow_direction()) == 1)
        self.assertTrue(result8.arrow_direction()[0].almost_equal(vector))

    def test_raise(self):
        with self.assertRaises(ValueError):
            strategy = FixHeadArrowFactory(0, 2, 1)
        with self.assertRaises(ValueError):
            strategy = FixHeadArrowFactory(-1, 2, 1)
        with self.assertRaises(ValueError):
            strategy = FixHeadArrowFactory(1, 1, 1)
        with self.assertRaises(ValueError):
            strategy = FixHeadArrowFactory(1, 0, 1)
        with self.assertRaises(ValueError):
            strategy = FixHeadArrowFactory(1, 0, 0)


class FixRatioStrategyTest(TestCase):
    def test_origin_and_vector(self):
        strategy = FixRatioArrowFactory(0.75, 2)
        vector = Vector(1, 0)
        result = strategy.from_origin_and_vector((0, 0), vector, 2, 1)
        self.assertTrue(result.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertTrue(len(result.coords) == 3)
        self.assertTrue(result.coords == [(0, 0), (1.5, 0), (2, 0)])
        self.assertFalse(result.is_closed)
        self.assertTrue(len(result.arrow_direction()) == 1)
        self.assertTrue(result.arrow_direction()[0].almost_equal(Vector(0.5, 0)))

        result1 = strategy.from_origin_and_vector((0, 0), vector, 2, 1, True)
        self.assertTrue(result1.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertTrue(len(result1.coords) == 3)
        self.assertTrue(result1.coords == [(2, 0), (0.5, 0), (0, 0)])
        self.assertFalse(result1.is_closed)
        self.assertTrue(len(result1.arrow_direction()) == 1)
        self.assertTrue(result1.arrow_direction()[0].invert().almost_equal(Vector(0.5, 0)))

    def test_straight_line(self):
        strategy = FixRatioArrowFactory(0.75, 2)
        straight_line = StraightSegment([(0, 0), (2, 0)])
        result2 = strategy.from_straight_line(straight_line, 2)
        self.assertTrue(result2.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result2.is_closed)
        self.assertTrue(len(result2.coords) == 3)
        self.assertTrue(len(result2.arrow_direction()) == 1)
        self.assertTrue(result2.arrow_direction()[0].almost_equal(Vector(0.5, 0)))

        result3 = strategy.from_straight_line(straight_line, 2, True)
        self.assertTrue(result3.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result3.is_closed)
        self.assertTrue(len(result3.coords) == 3)
        self.assertTrue(len(result3.arrow_direction()) == 1)
        self.assertTrue(result3.arrow_direction()[0].invert().almost_equal(Vector(0.5, 0)))

    def test_line(self):
        strategy = FixRatioArrowFactory(0.75, 2)
        line = LineString([(0, 0), (2, 0)])
        result4 = strategy.from_straight_line(line, 2)
        self.assertTrue(result4.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result4.is_closed)
        self.assertTrue(len(result4.coords) == 3)
        self.assertTrue(len(result4.arrow_direction()) == 1)
        self.assertTrue(result4.arrow_direction()[0].almost_equal(Vector(0.5, 0)))

        result5 = strategy.from_straight_line(line, 2, True)
        self.assertTrue(result5.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result5.is_closed)
        self.assertTrue(len(result5.coords) == 3)
        self.assertTrue(len(result5.arrow_direction()) == 1)
        self.assertTrue(result5.arrow_direction()[0].invert().almost_equal(Vector(0.5, 0)))

        line1 = LineString([(0, 0), (1, 0), (2, 0)])
        result6 = strategy.from_straight_line(line1, 2)
        self.assertTrue(result6.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result6.is_closed)
        self.assertTrue(len(result6.coords) == 3)
        self.assertTrue(len(result6.arrow_direction()) == 1)
        self.assertTrue(result6.arrow_direction()[0].almost_equal(Vector(0.5, 0)))

        result7 = strategy.from_straight_line(line1, 2, True)
        self.assertTrue(result7.axis.equals(LineString([(0, 0), (2, 0)])))
        self.assertFalse(result7.is_closed)
        self.assertTrue(len(result7.coords) == 3)
        self.assertTrue(len(result7.arrow_direction()) == 1)
        self.assertTrue(result7.arrow_direction()[0].invert().almost_equal(Vector(0.5, 0)))

    def test_raise(self):
        with self.assertRaises(ValueError):
            strategy = FixRatioArrowFactory(0, 2)
        with self.assertRaises(ValueError):
            strategy = FixRatioArrowFactory(2, 2)
        with self.assertRaises(ValueError):
            strategy = FixRatioArrowFactory(0.5, 0)
