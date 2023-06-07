from unittest import TestCase

from shapely.extension.model.arrow import ArrowJoint, Arrow
from shapely.extension.model.vector import Vector
from shapely.geometry import LineString
from shapely import wkt
from shapely.extension.constant import MATH_EPS


class ArrowTest(TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            arrow = Arrow()

        with self.assertRaises(TypeError):
            arrow = Arrow([ArrowJoint((0, 0))])

        with self.assertRaises(TypeError):
            arrow = Arrow(ArrowJoint(0, 0), 0, 0)

        #       |\
        # ┌─────┘ \
        # └─────┐ /
        #       |/
        arrow2 = Arrow([ArrowJoint((0, 0), 0.5, 0), ArrowJoint((1, 0), 1, 0.5), ArrowJoint((2, 0), 0, 0)])
        self.assertTrue(len(arrow2.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0)]).equals(arrow2.axis))
        self.assertFalse(arrow2.is_closed)
        self.assertTrue(len(arrow2.arrow_direction()) == 1)
        self.assertTrue(arrow2.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))

        #          │\
        # ─────────┤ >
        #          │/
        arrow3 = Arrow([ArrowJoint((0, 0), 0, 0), ArrowJoint((1, 0), 1, 0), ArrowJoint((2, 0), 0, 0)])
        self.assertTrue(len(arrow3.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0)]).equals(arrow3.axis))
        self.assertTrue(arrow3.shape.is_valid)
        self.assertFalse(arrow3.is_closed)
        self.assertTrue(len(arrow3.arrow_direction()) == 1)
        self.assertTrue(arrow3.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))

        #         /\
        #        /  \
        # ──────/──  \
        arrow4 = Arrow([ArrowJoint((0, 0), 0, 0), ArrowJoint((1, 0), 1, 0), ArrowJoint((1, 1), 0, 0)])
        self.assertTrue(len(arrow4.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (1, 1)]).equals(arrow4.axis))
        self.assertTrue(arrow4.shape.is_valid)
        self.assertFalse(arrow4.is_closed)
        self.assertTrue(len(arrow4.arrow_direction()) == 1)
        self.assertTrue(arrow4.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (1, 1)))

        arrow5 = Arrow([ArrowJoint((0, 0), 0.5, 0), ArrowJoint((1, 0), 1, 0.5), ArrowJoint((1, 1), 0, 0)])
        self.assertTrue(len(arrow5.coords) == 3)
        self.assertTrue(LineString([(0, 0), (1, 0), (1, 1)]).equals(arrow5.axis))
        self.assertTrue(arrow5.shape.is_valid)
        self.assertFalse(arrow5.is_closed)
        self.assertTrue(len(arrow5.arrow_direction()) == 1)
        self.assertTrue(arrow5.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (1, 1)))

        # ◄────▲
        # │    │
        # │    │
        # ▼────►
        arrow6 = Arrow(
            [
                ArrowJoint((0, 0), 0, 0),
                ArrowJoint((1, 0), 1, 0),
                ArrowJoint((2, 0), 0, 0),
                ArrowJoint((2, 1), 1, 0),
                ArrowJoint((2, 2), 0, 0),
                ArrowJoint((1, 2), 1, 0),
                ArrowJoint((0, 2), 0, 0),
                ArrowJoint((0, 1), 1, 0),
                ArrowJoint((0, 0), 0, 0),
            ]
        )
        self.assertTrue(len(arrow6.coords) == 9)
        self.assertTrue(
            LineString([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1), (0, 0)]).equals(arrow6.axis)
        )
        self.assertTrue(arrow6.shape.is_valid)
        self.assertTrue(arrow6.is_closed)
        self.assertTrue(len(arrow6.arrow_direction()) == 4)
        self.assertTrue(arrow6.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))
        self.assertTrue(arrow6.arrow_direction()[1] == Vector.from_origin_to_target((2, 1), (2, 2)))
        self.assertTrue(arrow6.arrow_direction()[2] == Vector.from_origin_to_target((1, 2), (0, 2)))
        self.assertTrue(arrow6.arrow_direction()[3] == Vector.from_origin_to_target((0, 1), (0, 0)))

        arrow7 = Arrow(
            [
                ArrowJoint((0, 0), 0.5, 0),
                ArrowJoint((1, 0), 1, 0.5),
                ArrowJoint((2, 0), 0.5, 0),
                ArrowJoint((2, 1), 1, 0.5),
                ArrowJoint((2, 2), 0.5, 0),
                ArrowJoint((1, 2), 1, 0.5),
                ArrowJoint((0, 2), 0.5, 0),
                ArrowJoint((0, 1), 1, 0.5),
                ArrowJoint((0, 0), 0, 0),
            ]
        )
        self.assertTrue(len(arrow7.coords) == 9)
        self.assertTrue(
            LineString([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1), (0, 0)]).equals(arrow7.axis)
        )
        self.assertTrue(arrow7.shape.is_valid)
        self.assertTrue(arrow7.is_closed)
        self.assertTrue(len(arrow7.arrow_direction()) == 4)
        self.assertTrue(arrow7.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (2, 0)))
        self.assertTrue(arrow7.arrow_direction()[1] == Vector.from_origin_to_target((2, 1), (2, 2)))
        self.assertTrue(arrow7.arrow_direction()[2] == Vector.from_origin_to_target((1, 2), (0, 2)))
        self.assertTrue(arrow7.arrow_direction()[3] == Vector.from_origin_to_target((0, 1), (0, 0)))

        # ◄───►
        arrow8 = Arrow(
            [ArrowJoint((0, 0), 0, 0), ArrowJoint((1, 0), 0, 1), ArrowJoint((2, 0), 1, 0), ArrowJoint((3, 0), 0, 0)]
        )
        self.assertTrue(len(arrow8.coords) == 4)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0), (3, 0)]).equals(arrow8.axis))
        self.assertTrue(arrow8.shape.is_valid)
        self.assertFalse(arrow8.is_closed)
        self.assertTrue(len(arrow8.arrow_direction()) == 2)
        self.assertTrue(arrow8.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (0, 0)))
        self.assertTrue(arrow8.arrow_direction()[1] == Vector.from_origin_to_target((2, 0), (3, 0)))

        arrow9 = Arrow(
            [ArrowJoint((0, 0), 0, 0), ArrowJoint((1, 0), 0.5, 1), ArrowJoint((2, 0), 1, 0.5), ArrowJoint((3, 0), 0, 0)]
        )
        self.assertTrue(len(arrow9.coords) == 4)
        self.assertTrue(LineString([(0, 0), (1, 0), (2, 0), (3, 0)]).equals(arrow9.axis))
        self.assertTrue(arrow9.shape.is_valid)
        self.assertFalse(arrow9.is_closed)
        self.assertTrue(len(arrow9.arrow_direction()) == 2)
        self.assertTrue(arrow9.arrow_direction()[0] == Vector.from_origin_to_target((1, 0), (0, 0)))
        self.assertTrue(arrow9.arrow_direction()[1] == Vector.from_origin_to_target((2, 0), (3, 0)))

    def test_one_point(self):
        arrow = Arrow([ArrowJoint((0, 0), 0.5, 0.5)])
        self.assertTrue(arrow.arrow_direction() == [])
        self.assertTrue(len(arrow.coords) == 1)
        self.assertTrue(arrow.coords[0] == (0, 0))

    def test_two_points(self):
        # ┌───┐
        # └───┘
        arrow = Arrow([ArrowJoint((0, 0), 0.5, 0.5), ArrowJoint((1, 0), 0, 0.5)])
        self.assertTrue(arrow.arrow_direction() == [])
        self.assertTrue(len(arrow.coords) == 2)
        self.assertTrue(arrow.coords == [(0, 0), (1, 0)])

        # │\
        # │/
        arrow1 = Arrow([ArrowJoint((0, 0), 0.5, 0), ArrowJoint((1, 0), 0, 0)])
        self.assertTrue(arrow1.arrow_direction()[0] == Vector(1, 0))
        self.assertTrue(len(arrow1.coords) == 2)
        self.assertTrue(arrow1.coords == [(0, 0), (1, 0)])

    def test_consecutive_same_points(self):
        with self.assertRaises(ValueError):
            arrow = Arrow(
                [
                    ArrowJoint((0, 0), 0.5, 0),
                    ArrowJoint((1, 0), 1, 0.5),
                    ArrowJoint((1, 0), 1, 0.5),
                    ArrowJoint((2, 0), 0, 0),
                ]
            )
            self.assertTrue(arrow.shape)

    def test_curve_arrow(self):
        #    ▲
        #    |
        #    |
        # ───┘
        arrow = Arrow(
            [
                ArrowJoint((0, 0), 0.5, 0),
                ArrowJoint((1, 0), 0.5, 0.5),
                ArrowJoint((1, 1), 1, 0.5),
                ArrowJoint((1, 2), 0, 0),
            ]
        )
        poly = wkt.loads(
            "POLYGON ((0.75 1, 0.5 1, 1 2, 1.5 1, 1.25 1, 1.25 -0.25, 0 -0.25, 0 0.25, 0.75 0.25, 0.75 1))"
        )
        self.assertTrue(arrow.shape.equals_exact(poly, MATH_EPS))
        self.assertTrue(arrow.is_closed == False)
        self.assertTrue(arrow.axis.equals(wkt.loads("LINESTRING (0 0, 1 0, 1 1, 1 2)")))
        self.assertTrue(arrow.coords == [(0, 0), (1, 0), (1, 1), (1, 2)])
        self.assertTrue(arrow.arrow_direction() == [Vector.from_origin_to_target((1, 1), (1, 2))])

    def test_curve_arrow2(self):
        #      ▲
        # |\   |
        # | \  |
        # |  \ |
        # |   \|
        arrow = Arrow(
            [
                ArrowJoint((0, 0), 0.5, 0),
                ArrowJoint((0, 2), 0.5, 0.5),
                ArrowJoint((2, 0), 0.5, 0.5),
                ArrowJoint((2, 2), 1, 0.5),
                ArrowJoint((2, 3), 0, 0),
            ]
        )
        poly = wkt.loads(
            "POLYGON ((1.75 0.6035533905932737, 1.75 2, 1.5000000000000002 2, 2 3, 2.5 2, 2.25 2, 2.25 -0.6035533905932736, 0.25 1.396446609406726, 0.25 0, -0.25 0, -0.25 2.603553390593274, 1.75 0.6035533905932737))"
        )
        self.assertTrue(arrow.shape.equals_exact(poly, MATH_EPS))
        self.assertTrue(arrow.is_closed == False)
        self.assertTrue(arrow.axis.equals(wkt.loads("LINESTRING (0 0, 0 2, 2 0, 2 2, 2 3)")))
        self.assertTrue(arrow.coords == [(0, 0), (0, 2), (2, 0), (2, 2), (2, 3)])
        self.assertTrue(arrow.arrow_direction() == [Vector.from_origin_to_target((2, 2), (2, 3))])

    def test_circle_arrow(self):
        # ----
        # |  |
        # ▼  |
        # ----
        arrow = Arrow(
            [
                ArrowJoint((0, 0), 0.5, 0),
                ArrowJoint((1, 0), 0.5, 0.5),
                ArrowJoint((1, 1), 0.5, 0.5),
                ArrowJoint((0, 1), 0.5, 0.5),
                ArrowJoint((0, 0), 0, 0),
            ]
        )
        poly = wkt.loads(
            "POLYGON ((-0.2499999999999999 0.9999999999999999, 0 0.9999999999999999, 0 1.25, 1.25 1.25, 1.25 -0.25, 0 -0.25, 0 -0.0000000000000001, -0.2499999999999999 0.9999999999999999), (0.0625 0.25, 0.75 0.25, 0.75 0.75, 0.1875000000000001 0.75, 0.0625 0.25))"
        )
        self.assertTrue(arrow.shape.equals_exact(poly, MATH_EPS))
        self.assertTrue(arrow.is_closed)
        self.assertTrue(arrow.axis.equals(wkt.loads("LINESTRING (0 0, 1 0, 1 1, 0 1, 0 0)")))
        self.assertTrue(arrow.coords == [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        self.assertTrue(arrow.arrow_direction() == [Vector.from_origin_to_target((0, 1), (0, 0))])

    def test_circle_arrow2(self):
        #   /\
        #  /  \
        # |/    \
        # ──    ──
        # \    /|
        #  \  /
        #   \/
        arrow = Arrow(
            [
                ArrowJoint((1, 0), 0.5, 0),
                ArrowJoint((0.5, 0.5), 0.5, 0.5),
                ArrowJoint((0, 1), 0.5, 0.5),
                ArrowJoint((-0.5, 0.5), 1, 0.5),
                ArrowJoint((-1, 0), 0.5, 0),
                ArrowJoint((-0.5, -0.5), 0.5, 0.5),
                ArrowJoint((0, -1), 0.5, 0.5),
                ArrowJoint((0.5, -0.5), 1, 0.5),
                ArrowJoint((1, 0), 0, 0),
            ]
        )
        poly = wkt.loads(
            "POLYGON ((0.8535533905932737 -0.8535533905932737, 0.6767766952966369 -0.6767766952966369, 0 -1.353553390593274, -1.176776695296637 -0.1767766952966368, -0.9999999999999999 0.0000000000000002, -0.8535533905932737 0.8535533905932737, -0.6767766952966369 0.6767766952966369, 0 1.353553390593274, 1.176776695296637 0.1767766952966368, 0.9999999999999999 -0.0000000000000002, 0.8535533905932737 -0.8535533905932737), (0.1464466094067262 -0.1464466094067263, 0.6982233047033632 -0.0517766952966369, 0 0.6464466094067263, -0.323223304703363 0.3232233047033632, -0.1464466094067262 0.1464466094067263, -0.6982233047033632 0.0517766952966369, 0 -0.6464466094067263, 0.323223304703363 -0.3232233047033632, 0.1464466094067262 -0.1464466094067263))"
        )
        self.assertTrue(arrow.shape.equals_exact(poly, MATH_EPS))
        self.assertTrue(arrow.is_closed)
        self.assertTrue(
            arrow.axis.equals(
                wkt.loads("LINESTRING (1 0, 0.5 0.5, 0 1, -0.5 0.5, -1 0, -0.5 -0.5, 0 -1, 0.5 -0.5, 1 0)")
            )
        )
        self.assertTrue(
            arrow.coords
            == [(1, 0), (0.5, 0.5), (0, 1), (-0.5, 0.5), (-1, 0), (-0.5, -0.5), (0, -1), (0.5, -0.5), (1, 0)]
        )
        self.assertTrue(
            arrow.arrow_direction()
            == [Vector.from_origin_to_target((-0.5, 0.5), (-1, 0)), Vector.from_origin_to_target((0.5, -0.5), (1, 0))]
        )
