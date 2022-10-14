from unittest import TestCase

from shapely.extension.model.coord import Coord
from shapely.extension.model.stretch import Pivot, DirectEdge, StretchFactory
from shapely.extension.model.vector import Vector
from shapely.geometry import Point, LineString, box, Polygon


class StretchTest(TestCase):
    def test_pivot_isvalid(self):
        pivot = Pivot(origin=Coord((0, 0)))
        self.assertTrue(pivot.is_valid)

        pivot = Pivot(origin=(0, 0))
        self.assertTrue(pivot.is_valid)

        pivot = Pivot(origin=Point((0, 0)))
        self.assertTrue(pivot.is_valid)

        pivot.in_edges.append(LineString())
        self.assertFalse(pivot.is_valid)

    def test_edge_create(self):
        pivot_0 = Pivot(origin=Coord((0, 0)))
        pivot_1 = Pivot(origin=Coord((1, 1)))
        edge_0 = DirectEdge(from_p=pivot_0, to_p=pivot_1)
        edge_1 = DirectEdge(from_p=pivot_1, to_p=pivot_0)

        self.assertTrue(pivot_0.in_edges[0] == edge_1)
        self.assertTrue(pivot_0.out_edges[0] == edge_0)
        self.assertTrue(pivot_1.in_edges[0] == edge_0)
        self.assertTrue(pivot_1.out_edges[0] == edge_1)

        # 重复生成
        # 此现象是合法的. 在divided_by等中间过程中会重复生成相同的edge
        edge_2 = DirectEdge(from_p=pivot_0, to_p=pivot_1)
        edge_3 = DirectEdge(from_p=pivot_1, to_p=pivot_0)
        self.assertEqual(edge_2, edge_0)
        self.assertEqual(edge_3, edge_1)
        self.assertEqual(len(pivot_0.in_edges), 2)
        self.assertEqual(len(pivot_0.out_edges), 2)
        self.assertEqual(len(pivot_1.in_edges), 2)
        self.assertEqual(len(pivot_1.out_edges), 2)

    def test_pivot_single_move(self):
        pivot_0 = Pivot(origin=Coord((0, 0)))
        pivot_1 = Pivot(origin=Coord((1, 1)))
        edge_0 = DirectEdge(from_p=pivot_0, to_p=pivot_1)
        edge_1 = DirectEdge(from_p=pivot_1, to_p=pivot_0)

        target = Point((1, 2))
        pivot_1.move_to(target)
        self.assertTrue(pivot_1.origin == target)
        self.assertTrue(edge_0.to_p.origin == target)
        self.assertTrue(edge_1.from_p.origin == target)

        vector = Vector(x=1, y=0)
        pivot_0.move_by(vector)
        self.assertTrue(pivot_0.origin == Point((1, 0)))
        self.assertTrue(edge_0.from_p.origin == Point((1, 0)))
        self.assertTrue(edge_1.to_p.origin == Point((1, 0)))

    def test_stretch_create_by_single_poly(self):
        poly = box(0, 0, 1, 1)
        stretch = StretchFactory().create(poly)
        self.assertEqual(len(stretch.pivots), 4)
        self.assertEqual(len(stretch.edges), 4)
        self.assertEqual(len(stretch.closures), 1)
        self.assertEqual(stretch.closures[0].shape.area, 1)

    def test_stretch_create_by_invalid_poly(self):
        poly = box(0, 0, 0, 0)
        with self.assertRaises(ValueError):
            StretchFactory().create(poly)

        poly = Polygon()
        with self.assertRaises(ValueError):
            StretchFactory().create(poly)

        poly = Polygon(shell=((0, 0), (2, 0), (2, 2), (0, 2), (0, 0)),
                       holes=[((0.5, 0.5), (1, 0.5), (1, 1), (0.5, 1), (0.5, 0.5))])
        with self.assertRaises(ValueError):
            StretchFactory().create(poly)

    def test_stretch_create_by_polys(self):
        polys = [
            box(0, 0, 1, 1),
            box(1, 0, 2, 2),
            box(0, 1, 1, 3)
        ]
        stretch = StretchFactory().create(polys)

        self.assertEqual(len(stretch.pivots), 9)
        self.assertEqual(len(stretch.edges), 14)
        self.assertEqual(len(stretch.closures), 3)
        self.assertEqual(len(stretch.closures[0].edges), 4)
        self.assertEqual(len(stretch.closures[1].edges), 5)
        self.assertEqual(len(stretch.closures[2].edges), 5)
        self.assertEqual(stretch.closures[0].shape.area, 1)
        self.assertEqual(stretch.closures[1].shape.area, 2)
        self.assertEqual(stretch.closures[2].shape.area, 2)

    def test_stretch_create_by_polys_with_eps(self):
        polys = [
            box(0, 0, 1, 1),
            box(1.1, 0, 2, 2),
            box(0.1, 1, 1, 3)
        ]
        stretch = StretchFactory(dist_tol=0.5).create(polys)

        self.assertEqual(len(stretch.pivots), 9)
        self.assertEqual(len(stretch.edges), 14)
        self.assertEqual(len(stretch.closures), 3)
        self.assertEqual(len(stretch.closures[0].edges), 4)
        self.assertEqual(len(stretch.closures[1].edges), 5)
        self.assertEqual(len(stretch.closures[2].edges), 5)
        self.assertEqual(stretch.closures[0].shape.area, 1)
        self.assertEqual(stretch.closures[1].shape.area, 1.95)
        self.assertEqual(stretch.closures[2].shape.area, 2)

    def test_single_offset(self):
        poly = box(0, 0, 1, 1)
        stretch = StretchFactory().create(poly)
        stretch.edges[0].offset(-1)
        self.assertEqual(stretch.closures[0].shape.area, 2)
        stretch.edges[0].offset(1)
        self.assertEqual(stretch.closures[0].shape.area, 1)
        stretch.edges[0].offset(0)
        self.assertEqual(stretch.closures[0].shape.area, 1)

    def test_shared_offset(self):
        poly_0 = box(0, 0, 1, 1)
        poly_1 = box(1, 0, 2, 1)
        stretch = StretchFactory().create([poly_0, poly_1])

        stretch.edges[0].offset(0.5)
        self.assertEqual(len(stretch.edges), 8)
        self.assertEqual(stretch.closures[0].shape.area, 0.5)
        self.assertEqual(stretch.closures[1].shape.area, 1.5)

    def test_single_expand(self):
        poly = box(0, 0, 1, 1)
        stretch = StretchFactory().create(poly)

        stretch.edges[0].expand(Point(1, 0))
        self.assertEqual(len(stretch.edges), 4)
        self.assertEqual(stretch.closures[0].shape.area, 1)

        stretch.edges[0].expand(Point(2, 0))
        self.assertEqual(len(stretch.edges), 5)
        self.assertEqual(stretch.closures[0].shape.area, 1.5)

        stretch.edges[1].expand(Point(1, 0))
        self.assertEqual(len(stretch.edges), 6)
        self.assertEqual(stretch.closures[0].shape.area, 1)

    def test_bilateral_expand(self):
        poly_0 = box(0, 0, 1, 1)
        poly_1 = box(1, 0, 2, 1)
        stretch = StretchFactory().create([poly_0, poly_1])

        stretch.edges[0].expand(Point(1, 0))
        self.assertEqual(len(stretch.edges), 8)
        self.assertEqual(stretch.closures[0].shape.area, 1)
        self.assertEqual(stretch.closures[1].shape.area, 1)

        stretch.edges[0].expand(Point(1.5, 0.5))
        self.assertEqual(len(stretch.edges), 10)
        self.assertEqual(stretch.closures[0].shape.area, 1.25)
        self.assertEqual(stretch.closures[1].shape.area, 0.75)

    def test_interpolate(self):
        poly = box(0, 0, 8, 8)
        stretch = StretchFactory().create(poly)
        stretch.closures[0].edges[0].interpolate(1)
        self.assertEqual(stretch.closures[0].edges[0].shape.length, 1)
        self.assertEqual(stretch.closures[0].edges[1].shape.length, 7)

        poly = box(0, 0, 8, 8)
        stretch = StretchFactory().create(poly)
        stretch.closures[0].edges[0].interpolate(0.5, normalized=True)
        self.assertEqual(stretch.closures[0].edges[0].shape.length, 4)
        self.assertEqual(stretch.closures[0].edges[1].shape.length, 4)

    def test_divided_with_simple_poly(self):
        poly = box(0, 0, 4, 4)
        stretch = StretchFactory().create(poly)
        divider = LineString([(1, 0), (1, 4)])

        closures = stretch.closures[0].divided_by(divider)
        self.assertEqual(len(stretch.pivots), 6)
        self.assertEqual(len(stretch.edges), 8)
        self.assertEqual(len(stretch.closures), 2)
        self.assertEqual(closures[0].shape.area, 12)
        self.assertEqual(closures[1].shape.area, 4)

    def test_divided_with_complex_poly(self):
        poly = Polygon([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (2, 2), (2, 3), (0, 3), (0, 0)])
        stretch = StretchFactory().create(poly)
        divider = LineString([(1, 0), (1, 4)])

        closures = stretch.closures[0].divided_by(divider)
        self.assertEqual(len(stretch.pivots), 10)
        self.assertEqual(len(stretch.edges), 14)
        self.assertEqual(len(stretch.closures), 3)
        self.assertEqual(closures[0].shape.area, 3)
        self.assertEqual(closures[1].shape.area, 1)
        self.assertEqual(closures[2].shape.area, 1)

    def test_divided_by_multiline(self):
        poly = box(0, 0, 4, 4)
        stretch = StretchFactory().create(poly)
        divider = [LineString([(0, 0), (4, 4)]),
                   LineString([(0, 4), (4, 0)])]

        closures = stretch.closures[0].divided_by(divider)
        self.assertEqual(len(stretch.pivots), 5)
        self.assertEqual(len(stretch.edges), 12)
        self.assertEqual(len(stretch.closures), 4)
        self.assertEqual(closures[0].shape.area, 4)
        self.assertEqual(closures[1].shape.area, 4)
        self.assertEqual(closures[2].shape.area, 4)
        self.assertEqual(closures[3].shape.area, 4)
