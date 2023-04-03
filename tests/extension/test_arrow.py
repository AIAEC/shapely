from unittest import TestCase

from shapely.extension.model.arrow import Arrow
from shapely.extension.model.vector import Vector
from shapely.geometry import LineString, box, Polygon


class ArrowTest(TestCase):
    def test_init(self):
        arrow = Arrow()
        with self.assertRaises(ValueError):
            self.assertTrue(len(arrow.coords) == 0)
        with self.assertRaises(ValueError):
            self.assertTrue(arrow.axis == LineString())

        arrow1 = Arrow([(0, 0)])
        with self.assertRaises(ValueError):
            arrow_shape = arrow1.shape
        with self.assertRaises(ValueError):
            arrow_axis = arrow1.axis
        with self.assertRaises(ValueError):
            is_closed = arrow1.is_closed

        #       |\
        # ┌─────┘ \
        # └─────┐ /
        #       |/
        arrow2 = Arrow([(0, 0), (1, 0), (2, 0)], [(0.5, 0), (1, 0.5), (0, 0)])
        self.assertTrue(len(arrow2.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0)]).equals(arrow2.axis))
        self.assertFalse(arrow2.is_closed)
        self.assertTrue(len(arrow2.shafts()) == 1)
        self.assertTrue(len(arrow2.heads()) == 1)
        self.assertTrue(len(arrow2.arrow_direction()) == 1)
        self.assertTrue(arrow2.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))

        #          │\
        # ─────────┤ >
        #          │/
        arrow3 = Arrow([(0, 0), (1, 0), (2, 0)], [(0, 0), (1, 0), (0, 0)])
        self.assertTrue(len(arrow3.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0)]).equals(arrow3.axis))
        self.assertTrue(arrow3.shape.is_valid)
        self.assertFalse(arrow3.is_closed)
        self.assertTrue(len(arrow3.shafts()) == 1)
        self.assertTrue(len(arrow3.heads()) == 1)
        self.assertTrue(len(arrow3.arrow_direction()) == 1)
        self.assertTrue(arrow3.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))

        #         /\
        #        /  \
        # ──────/──  \
        arrow4 = Arrow([(0, 0), (1, 0), (1, 1)], [(0, 0), (1, 0), (0, 0)])
        self.assertTrue(len(arrow4.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (1, 1)]).equals(arrow4.axis))
        self.assertTrue(arrow4.shape.is_valid)
        self.assertFalse(arrow4.is_closed)
        self.assertTrue(len(arrow4.shafts()) == 1)
        self.assertTrue(len(arrow4.heads()) == 1)
        self.assertTrue(len(arrow4.arrow_direction()) == 1)
        self.assertTrue(arrow4.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (1, 1)))
        
        arrow5 = Arrow([(0, 0), (1, 0), (1, 1)], [(0.5, 0), (1, 0.5), (0, 0)])
        self.assertTrue(len(arrow5.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (1, 1)]).equals(arrow5.axis))
        self.assertTrue(arrow5.shape.is_valid)
        self.assertFalse(arrow5.is_closed)
        self.assertTrue(len(arrow5.shafts()) == 1)
        self.assertTrue(len(arrow5.heads()) == 1)
        self.assertTrue(len(arrow5.arrow_direction()) == 1)
        self.assertTrue(arrow5.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (1, 1)))

        # ◄────▲
        # │    │
        # │    │
        # ▼────►
        arrow6 = Arrow([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1), (0, 0)],
                       [(0, 0), (1, 0), (0, 0), (1, 0), (0, 0), (1, 0), (0, 0), (1, 0), (0, 0)])
        self.assertTrue(len(arrow6.coords) == 9)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1), (0, 0)])
                        .equals(arrow6.axis))
        self.assertTrue(arrow6.shape.is_valid)
        self.assertTrue(arrow6.is_closed)
        self.assertTrue(len(arrow6.shafts()) == 4)
        self.assertTrue(len(arrow6.heads()) == 4)
        self.assertTrue(len(arrow6.arrow_direction()) == 4)
        self.assertTrue(arrow6.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))
        self.assertTrue(arrow6.arrow_direction()[1] == Vector.from_origin_to_target((2, 1), (2, 2)))
        self.assertTrue(arrow6.arrow_direction()[2] == Vector.from_origin_to_target((1, 2), (0, 2)))
        self.assertTrue(arrow6.arrow_direction()[3] == Vector.from_origin_to_target((0, 1), (0, 0)))
        
        arrow7 = Arrow([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1), (0, 0)],
                       [(0.5, 0), (1, 0.5), (0.5, 0), (1, 0.5), (0.5, 0), (1, 0.5), (0.5, 0), (1, 0.5), (0, 0)])
        self.assertTrue(len(arrow7.coords) == 9)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1), (0, 0)])
                        .equals(arrow7.axis))
        self.assertTrue(arrow7.shape.is_valid)
        self.assertTrue(arrow7.is_closed)
        self.assertTrue(len(arrow7.shafts()) == 4)
        self.assertTrue(len(arrow7.heads()) == 4)
        self.assertTrue(len(arrow7.arrow_direction()) == 4)
        self.assertTrue(arrow7.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))
        self.assertTrue(arrow7.arrow_direction()[1] == Vector.from_origin_to_target((2, 1), (2, 2)))
        self.assertTrue(arrow7.arrow_direction()[2] == Vector.from_origin_to_target((1, 2), (0, 2)))
        self.assertTrue(arrow7.arrow_direction()[3] == Vector.from_origin_to_target((0, 1), (0, 0)))

        # ◄───►
        arrow8 = Arrow([(0, 0), (1, 0), (2, 0), (3, 0)], [(0, 0), (0, 1), (1, 0), (0, 0)])
        self.assertTrue(len(arrow8.coords) == 4)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0), (3, 0)]).equals(arrow8.axis))
        self.assertTrue(arrow8.shape.is_valid)
        self.assertFalse(arrow8.is_closed)
        self.assertTrue(len(arrow8.shafts()) == 1)
        self.assertTrue(len(arrow8.heads()) == 2)
        self.assertTrue(len(arrow8.arrow_direction()) == 2)
        self.assertTrue(arrow8.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (0, 0)))
        self.assertTrue(arrow8.arrow_direction()[1] == Vector.from_origin_to_target((2, 0), (3, 0)))

        arrow9 = Arrow([(0, 0), (1, 0), (2, 0), (3, 0)], [(0, 0), (0.5, 1), (1, 0.5), (0, 0)])
        self.assertTrue(len(arrow9.coords) == 4)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0), (3, 0)]).equals(arrow9.axis))
        self.assertTrue(arrow9.shape.is_valid)
        self.assertFalse(arrow9.is_closed)
        self.assertTrue(len(arrow9.shafts()) == 1)
        self.assertTrue(len(arrow9.heads()) == 2)
        self.assertTrue(len(arrow9.arrow_direction()) == 2)
        self.assertTrue(arrow9.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (0, 0)))
        self.assertTrue(arrow9.arrow_direction()[1] == Vector.from_origin_to_target((2, 0), (3, 0)))

    def test_one_point(self):
        arrow = Arrow([(0, 0)], [(0.5, 0.5)])
        self.assertTrue(arrow.arrow_direction() == [])
        self.assertTrue(len(arrow.coords) == 1)
        self.assertTrue(arrow.coords[0] == (0, 0))
        self.assertTrue(arrow.heads() == [])
        self.assertTrue(arrow.shafts() == [])

    def test_two_points(self):
        # ┌───┐
        # └───┘
        arrow = Arrow([(0, 0), (1, 0)], [(0.5, 0.5), (0, 0.5)])
        self.assertTrue(arrow.arrow_direction() == [])
        self.assertTrue(len(arrow.coords) == 2)
        self.assertTrue(arrow.coords == [(0, 0), (1, 0)])
        self.assertTrue(arrow.heads() == [])
        self.assertTrue(len(arrow.shafts()) == 1)
        self.assertTrue(arrow.shafts()[0].equals(box(0, -0.25, 1, 0.25)))

        # │\
        # │/
        arrow1 = Arrow([(0, 0), (1, 0)], [(0.5, 0), (0, 0)])
        self.assertTrue(arrow1.arrow_direction()[0] == Vector(1, 0))
        self.assertTrue(len(arrow1.coords) == 2)
        self.assertTrue(arrow1.coords == [(0, 0), (1, 0)])
        self.assertTrue(len(arrow1.heads()) == 1)
        self.assertTrue(arrow1.heads()[0].equals(Polygon([(0, -0.25), (0, 0.25), (1, 0)])))
        self.assertTrue(len(arrow1.shafts()) == 0)
