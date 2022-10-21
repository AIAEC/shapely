from math import isclose
from unittest import TestCase

from shapely.extension.model.coord import Coord
from shapely.extension.model.stretch import Pivot, DirectEdge, StretchFactory, Closure, MultiDirectEdge, Stretch
from shapely.extension.model.vector import Vector
from shapely.extension.util.iter_util import first, win_slice
from shapely.geometry import Point, LineString, box, Polygon
from shapely.wkt import loads


class PivotTest(TestCase):
    def test_pivot_in_out_edges(self):
        pass

    def test_pivot_stretch_attributes(self):
        pass

    def test_pivot_attributes(self):
        pivot = Pivot(Coord(0, 0))
        self.assertTrue(isinstance(pivot.shape, Point))
        self.assertIsNone(pivot.stretch)

    def test_pivot_isvalid(self):
        pivot = Pivot(origin=Coord((0, 0)))
        self.assertTrue(pivot.is_valid)

        pivot = Pivot(origin=(0, 0))
        self.assertTrue(pivot.is_valid)

        pivot = Pivot(origin=Point((0, 0)))
        self.assertTrue(pivot.is_valid)

        pivot.in_edges.append(LineString())
        self.assertFalse(pivot.is_valid)

        with self.assertRaises(ValueError):
            Pivot(Point())

        with self.assertRaises(TypeError):
            Pivot(None)

    def test_pivot_single_move(self):
        pivot_0 = Pivot(origin=Coord((0, 0)))
        pivot_1 = Pivot(origin=Coord((1, 1)))
        edge_0 = DirectEdge(from_pivot=pivot_0, to_pivot=pivot_1)
        edge_1 = DirectEdge(from_pivot=pivot_1, to_pivot=pivot_0)

        with self.assertRaises(TypeError):
            pivot_0.move_to(None)

        target = Point(1, 2)
        pivot_1.move_to(target)
        self.assertEqual(pivot_1.shape, target)
        self.assertEqual(edge_0._to_pivot.shape, target)
        self.assertEqual(edge_0._from_pivot.shape, Point(0, 0))
        self.assertEqual(edge_1._from_pivot.shape, target)
        self.assertEqual(edge_1._to_pivot.shape, Point(0, 0))

        vector = Vector(x=1, y=0)
        pivot_0.move_by(vector)
        self.assertEqual(pivot_0.shape, Point(1, 0))
        self.assertEqual(edge_0._from_pivot.shape, Point(1, 0))
        self.assertEqual(edge_0._to_pivot.shape, Point(1, 2))
        self.assertEqual(edge_1._to_pivot.shape, Point(1, 0))
        self.assertEqual(edge_1._from_pivot.shape, Point(1, 2))

        pivot_0.move_by(Vector.zero())
        self.assertEqual(pivot_0.shape, Point(1, 0))

        with self.assertRaises(TypeError):
            pivot_0.move_by(None)

    def test_intersects(self):
        pivot_0 = Pivot(origin=Coord((0, 0)))
        pivot_1 = Pivot(origin=Coord((1, 1)))

        self.assertTrue(pivot_1.intersects(pivot_1))
        self.assertFalse(pivot_1.intersects(pivot_0))
        self.assertTrue(pivot_0.intersects(Pivot(origin=Coord((0, 0)))))


class DirectEdgeTest(TestCase):

    def test_intersects(self):
        pivot_0 = Pivot(origin=Coord((0, 0)))
        pivot_1 = Pivot(origin=Coord((1, 1)))

        edge_0 = DirectEdge(from_pivot=pivot_0, to_pivot=pivot_1)
        edge_1 = DirectEdge(from_pivot=pivot_1, to_pivot=pivot_0)

        self.assertTrue(edge_0.intersects(edge_1))

        pivot_2 = Pivot(origin=Coord((0, 1)))
        pivot_3 = Pivot(origin=Coord((1, 0)))
        edge_2 = DirectEdge(from_pivot=pivot_2, to_pivot=pivot_3)
        self.assertFalse(edge_0.intersects(edge_2))

        edge_3 = DirectEdge(from_pivot=pivot_1, to_pivot=pivot_3)

        self.assertEqual(edge_1, edge_0.intersection(edge_1))
        self.assertEqual(pivot_1, edge_3.intersection(edge_0))

    def test_edge_create(self):
        pivot_0 = Pivot(origin=Coord((0, 0)))
        pivot_1 = Pivot(origin=Coord((1, 1)))

        with self.assertRaises(ValueError):
            DirectEdge(from_pivot=pivot_0, to_pivot=pivot_0)

        edge_0 = DirectEdge(from_pivot=pivot_0, to_pivot=pivot_1)
        edge_1 = DirectEdge(from_pivot=pivot_1, to_pivot=pivot_0)
        self.assertIsNone(edge_0.stretch)
        self.assertIsNone(edge_1.stretch)
        self.assertEqual(1, len(pivot_0.in_edges))
        self.assertEqual(1, len(pivot_0.out_edges))
        self.assertEqual(1, len(pivot_1.in_edges))
        self.assertEqual(1, len(pivot_1.out_edges))
        self.assertEqual(pivot_0.in_edges[0], edge_1)
        self.assertEqual(pivot_0.out_edges[0], edge_0)
        self.assertEqual(pivot_1.in_edges[0], edge_0)
        self.assertEqual(pivot_1.out_edges[0], edge_1)

        # 重复生成: 理应无法生成冗余的direct edge
        edge_2 = DirectEdge(from_pivot=pivot_0, to_pivot=pivot_1)
        edge_3 = DirectEdge(from_pivot=pivot_1, to_pivot=pivot_0)
        self.assertEqual(edge_2, edge_0)
        self.assertEqual(edge_3, edge_1)
        self.assertEqual(1, len(pivot_0.in_edges))
        self.assertEqual(1, len(pivot_0.out_edges))
        self.assertEqual(1, len(pivot_1.in_edges))
        self.assertEqual(1, len(pivot_1.out_edges))
        self.assertEqual(pivot_0.in_edges[0], edge_1)
        self.assertEqual(pivot_0.out_edges[0], edge_0)
        self.assertEqual(pivot_1.in_edges[0], edge_0)
        self.assertEqual(pivot_1.out_edges[0], edge_1)

    def test_single_offset(self):
        poly = box(0, 0, 1, 1)
        stretch = StretchFactory().create(poly)
        target_edge = min(stretch.edges, key=lambda edge: edge.shape.centroid.y)
        target_edge.offset(-1)
        self.assertTrue(stretch.closures[0].shape.equals(box(0, -1, 1, 1)))
        target_edge.offset(1)
        self.assertTrue(stretch.closures[0].shape.equals(poly))
        target_edge.offset(0)
        self.assertTrue(stretch.closures[0].shape.equals(poly))

    def test_shared_offset(self):
        poly_0 = box(0, 0, 1, 1)
        poly_1 = box(1, 0, 2, 1)
        stretch = StretchFactory().create([poly_0, poly_1])

        target_closure = min(stretch.closures, key=lambda closure: closure.shape.centroid.x)
        target_edge = first(lambda edge: isclose(edge.shape.centroid.x, 1) and edge.closure is target_closure,
                            stretch.edges)

        self.assertEqual(len(stretch.edges), 8)
        self.assertTrue(stretch.closures[0].shape.equals(poly_0))
        self.assertTrue(stretch.closures[1].shape.equals(poly_1))

        target_edge.offset(0.5)

        self.assertEqual(len(stretch.edges), 8)
        self.assertTrue(stretch.closures[0].shape.equals(box(0, 0, 0.5, 1)))
        self.assertTrue(stretch.closures[1].shape.equals(box(0.5, 0, 2, 1)))

        with self.assertRaises(TypeError):
            target_edge.offset(None)

    def test_single_expand(self):
        poly = box(0, 0, 1, 1)
        stretch = StretchFactory().create(poly)

        self.assertEqual(1, len(stretch.closures))
        self.assertEqual(4, len(stretch.pivots))
        self.assertEqual(4, len(stretch.edges))

        # expand by endpoint of the edge
        target_edge = max(stretch.edges, key=lambda edge: edge.shape.centroid.x)
        expanded_edges = target_edge.expand(Point(1, 0))
        self.assertEqual(1, len(expanded_edges))
        self.assertEqual(4, len(stretch.edges))
        self.assertEqual(4, len(stretch.pivots))
        self.assertEqual(1, len(stretch.closures))
        self.assertTrue(stretch.closures[0].shape.equals(poly))

        # expand by point that nearby endpoint of the edge
        expanded_edges = target_edge.expand(Point(1 + 1e-6, 0), dist_tol=1e-5)
        self.assertEqual(1, len(expanded_edges))
        self.assertEqual(4, len(stretch.edges))
        self.assertEqual(4, len(stretch.pivots))
        self.assertEqual(1, len(stretch.closures))
        self.assertTrue(stretch.closures[0].shape.equals(poly))

        # expand by point outside edge
        expanded_edges = target_edge.expand(Point(2, 0))
        self.assertEqual(2, len(expanded_edges))
        self.assertEqual(5, len(stretch.edges))
        self.assertEqual(5, len(stretch.pivots))
        self.assertEqual(1, len(stretch.closures))
        self.assertTrue(stretch.closures[0].shape.equals(loads('POLYGON ((1 0, 2 0, 1 1, 0 1, 0 0, 1 0))')))

        # TODO: expand same point several time
        # TODO: test new pivot's edge relationship

    def test_bilateral_expand(self):
        poly_0 = box(0, 0, 1, 1)
        poly_1 = box(1, 0, 2, 1)
        stretch = StretchFactory().create([poly_0, poly_1])

        self.assertEqual(6, len(stretch.pivots))
        self.assertEqual(8, len(stretch.edges))
        self.assertEqual(2, len(stretch.closures))

        target_edge = first(lambda edge: isclose(edge.shape.centroid.x, 1), stretch.edges)

        expanded_edges = target_edge.expand(Point(1, 0))
        self.assertEqual(1, len(expanded_edges))
        self.assertEqual(6, len(stretch.pivots))
        self.assertEqual(8, len(stretch.edges))
        self.assertEqual(2, len(stretch.closures))

        expanded_edges = target_edge.expand(Point(1.5, 0.5))
        self.assertEqual(len(expanded_edges), 2)
        self.assertEqual(len(stretch.edges), 10)
        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(7, len(stretch.pivots))
        self.assertTrue(stretch.closures[0].shape.equals(loads('POLYGON ((1 0, 1.5 0.5, 1 1, 0 1, 0 0, 1 0))')))
        self.assertTrue(stretch.closures[1].shape.equals(loads('POLYGON ((2 0, 2 1, 1 1, 1.5 0.5, 1 0, 2 0))')))

        # TODO: expand same point several time
        # TODO: test new pivot's edge relationship

    def test_single_interpolate(self):
        poly = box(0, 0, 8, 8)
        stretch = StretchFactory().create(poly)
        new_edges = stretch.closures[0]._edges[0].interpolate(1)
        self.assertEqual(new_edges[0].shape.length, 1)
        self.assertEqual(new_edges[1].shape.length, 7)

        poly = box(0, 0, 8, 8)
        stretch = StretchFactory().create(poly)
        new_edges = stretch.closures[0]._edges[0].interpolate(0.5, absolute=False)
        self.assertEqual(new_edges[0].shape.length, 4)
        self.assertEqual(new_edges[1].shape.length, 4)

    def test_bilateral_interpolate(self):
        poly_0 = box(0, 0, 8, 8)
        poly_1 = box(8, 0, 16, 8)
        stretch = StretchFactory().create([poly_0, poly_1])

        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(6, len(stretch.pivots))
        self.assertEqual(8, len(stretch.edges))

        target_edge = first(lambda edge: isclose(edge.shape.centroid.x, 8), stretch.edges)
        new_edges = target_edge.interpolate(0)
        self.assertEqual(len(new_edges), 1)
        self.assertEqual(new_edges[0].shape.length, 8)

        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(6, len(stretch.pivots))
        self.assertEqual(8, len(stretch.edges))

        new_edges = target_edge.interpolate(3)
        self.assertEqual(len(new_edges), 2)
        self.assertEqual(new_edges[0].shape.length, 3)
        self.assertEqual(new_edges[1].shape.length, 5)
        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(7, len(stretch.pivots))
        self.assertEqual(10, len(stretch.edges))


class ClosureTest(TestCase):
    def test_closure_create_for_simple_valid_case(self):
        pivots = [Pivot(Point(0, 0)), Pivot(Point(1, 0)), Pivot(Point(1, 1))]
        edges = [DirectEdge(pivots[0], pivots[1]),
                 DirectEdge(pivots[1], pivots[2]),
                 DirectEdge(pivots[2], pivots[0])]
        closure = Closure(edges)
        self.assertTrue(isinstance(closure, Closure))
        self.assertEqual(3, len(closure.pivots))
        self.assertEqual(3, len(closure._edges))
        self.assertTrue(closure.shape.equals(Polygon([(0, 0), (1, 0), (1, 1)])))

    def test_closure_create_for_disordered_edges(self):
        pivots = [Pivot(Point(0, 0)), Pivot(Point(1, 0)), Pivot(Point(1, 1)), Pivot(Point(0, 1))]
        valid_edges = [DirectEdge(pivots[0], pivots[1]),
                       DirectEdge(pivots[2], pivots[3]),
                       DirectEdge(pivots[1], pivots[2]),
                       DirectEdge(pivots[3], pivots[0])]
        closure = Closure(valid_edges)
        self.assertTrue(isinstance(closure, Closure))
        self.assertEqual(4, len(closure.pivots))
        self.assertEqual(4, len(closure._edges))
        self.assertTrue(closure.shape.equals(box(0, 0, 1, 1)))

        invalid_edges = [DirectEdge(pivots[0], pivots[1]),
                         DirectEdge(pivots[2], pivots[3]),
                         DirectEdge(pivots[2], pivots[1]),
                         DirectEdge(pivots[3], pivots[0])]
        with self.assertRaises(ValueError):
            Closure(invalid_edges)

    def test_create_closure(self):
        pivots = [Pivot(Point(1, 1)), Pivot(Point(0, 1)), Pivot(Point(0, 0)), Pivot(Point(1, 0))]
        valid_edges = [DirectEdge(pivots[0], pivots[1]),
                       DirectEdge(pivots[2], pivots[3]),
                       DirectEdge(pivots[1], pivots[2]),
                       DirectEdge(pivots[3], pivots[0])]
        closure = Closure(valid_edges)
        self.assertTrue(isinstance(closure, Closure))
        self.assertEqual(4, len(closure.pivots))
        self.assertEqual(4, len(closure._edges))
        self.assertTrue(closure.shape.equals(box(0, 0, 1, 1)))

    def test_closure_attributes(self):
        pass

    def test_split_to_halves_by_edge(self):
        # split by direct edge into 2 halves
        pivots = [Pivot(Point(0, 0)), Pivot(Point(1, 0)), Pivot(Point(1, 1)), Pivot(Point(0, 1))]
        valid_edges = [DirectEdge(pivots[0], pivots[1]),
                       DirectEdge(pivots[2], pivots[3]),
                       DirectEdge(pivots[1], pivots[2]),
                       DirectEdge(pivots[3], pivots[0])]
        closure = Closure(valid_edges)
        result = closure.split_to_halves(DirectEdge(pivots[0], pivots[2]))
        self.assertEqual(2, len(result))
        self.assertTrue(all(isinstance(item, Closure) for item in result))
        self.assertEqual(0.5, result[0].shape.area)
        self.assertEqual(0.5, result[1].shape.area)
        result.sort(key=lambda cls: cls.shape.centroid.x)
        self.assertTrue(result[0].shape.equals(Polygon([(0, 0), (1, 1), (0, 1)])))
        self.assertTrue(result[1].shape.equals(Polygon([(0, 0), (1, 0), (1, 1)])))

        # TODO: test new closures' attributes

    def test_split_to_halves_by_multi_edge(self):
        # split by multi direct edge into 2 halves
        pivots = [Pivot(Point(0, 0)), Pivot(Point(1, 0)), Pivot(Point(1, 1)), Pivot(Point(0, 1)),
                  Pivot(Point(0.5, 0.5))]
        valid_edges = [DirectEdge(pivots[0], pivots[1]),
                       DirectEdge(pivots[2], pivots[3]),
                       DirectEdge(pivots[1], pivots[2]),
                       DirectEdge(pivots[3], pivots[0])]
        closure = Closure(valid_edges)
        multi_edge = MultiDirectEdge([
            DirectEdge(pivots[0], pivots[4]),
            DirectEdge(pivots[4], pivots[2])
        ])
        result = closure.split_to_halves(multi_edge)
        self.assertEqual(2, len(result))
        self.assertTrue(all(isinstance(item, Closure) for item in result))
        self.assertEqual(0.5, result[0].shape.area)
        self.assertEqual(0.5, result[1].shape.area)
        result.sort(key=lambda cls: cls.shape.centroid.x)
        self.assertTrue(result[0].shape.equals(Polygon([(0, 0), (0.5, 0.5), (1, 1), (0, 1)])))
        self.assertTrue(result[1].shape.equals(Polygon([(0, 0), (1, 0), (1, 1), (0.5, 0.5), (0, 0)])))

        # TODO: test new closures' attributes

    def test_split_to_halves_when_edge_on_closure(self):
        # cut by linestring that actually is the edge of the closure, which will return the origin closure
        pivots = [Pivot(Point(0, 0)), Pivot(Point(1, 0)), Pivot(Point(1, 1))]
        valid_edges = [DirectEdge(pivots[0], pivots[1]),
                       DirectEdge(pivots[1], pivots[2]),
                       DirectEdge(pivots[2], pivots[0])]
        closure = Closure(valid_edges)
        result = closure.split_to_halves(DirectEdge(pivots[2], pivots[0]))
        self.assertEqual(1, len(result))
        self.assertTrue(all(isinstance(item, Closure) for item in result))
        self.assertTrue(result[0].shape.equals(Polygon([(0, 0), (1, 0), (1, 1)])))

    def test_split_to_halves_when_edge_extrude_outside_of_closure(self):
        # cut by linestring that extrude the closure, which will return the origin closure
        poly = loads('POLYGON ((1 0, 0 0, 0 2, 1 2, 1 1.5, 0.5 1.5, 0.5 0.5, 1 0.5, 1 0))')
        pivots = poly.ext.decompose(Point).drop_right(1).map(Pivot).to_list()
        valid_edges = [DirectEdge(p, np) for p, np in win_slice(pivots, win_size=2, tail_cycling=True)]
        closure = Closure(valid_edges)
        self.assertEqual(Point(1, 1.5), pivots[4].shape)
        self.assertEqual(Point(1, 0.5), pivots[7].shape)
        result = closure.split_to_halves(DirectEdge(pivots[4], pivots[7]))
        self.assertEqual(1, len(result))
        self.assertTrue(all(isinstance(item, Closure) for item in result))
        self.assertTrue(result[0].shape.equals(poly))

    def test_split_by(self):
        poly = loads('POLYGON ((0.5 1.5, 1 1.5, 1 2, 0.5 2, -0.5 2, -0.5 0.5, -0.5 0, 0 0, 0 1, 0 1.5, 0.5 1.5))')
        pivots = poly.ext.decompose(Point).drop_right(1).map(Pivot).to_list()
        valid_edges = [DirectEdge(p, np) for p, np in win_slice(pivots, win_size=2, tail_cycling=True)]
        closure = Closure(valid_edges)
        self.assertEqual(Point(0.5, 2), pivots[3].shape)
        self.assertEqual(Point(0.5, 1.5), pivots[0].shape)
        self.assertEqual(Point(0, 1), pivots[8].shape)
        self.assertEqual(Point(-0.5, 0.5), pivots[5].shape)
        splitter = MultiDirectEdge([
            DirectEdge(pivots[3], pivots[0]),
            DirectEdge(pivots[0], pivots[8]),
            DirectEdge(pivots[8], pivots[5]),
        ])

        result = closure.split_by(splitter)
        self.assertEqual(3, len(result))
        self.assertTrue(all(isinstance(item, Closure) for item in result))

        result.sort(key=lambda cls: cls.shape.centroid.y)
        self.assertTrue(result[0].shape.equals(Polygon([(0, 0), (0, 1), (-0.5, 0.5), (-0.5, 0)])))
        self.assertTrue(
            result[1].shape.equals(Polygon([(0, 1), (0, 1.5), (0.5, 1.5), (0.5, 2), (-0.5, 2), (-0.5, 0.5)])))
        self.assertTrue(result[2].shape.equals(Polygon([(0.5, 1.5), (1, 1.5), (1, 2), (0.5, 2)])))

    def test_map_to_edge(self):
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        pivots = poly.ext.decompose(Point).drop_right(1).map(Pivot).to_list()
        valid_edges = [DirectEdge(p, np) for p, np in win_slice(pivots, win_size=2, tail_cycling=True)]
        closure = Closure(valid_edges)

        result = closure.map_to_edge(LineString([(0, 0), (1, 1)]))
        self.assertTrue(isinstance(result, MultiDirectEdge))
        self.assertEqual(1, len(result.edges))
        self.assertTrue(result.pivots[0] is pivots[0])

        # TODO: test edge's attributes

    def test_divided_by_lines(self):
        poly = Polygon([(0, 0), (100, 0), (100, 10), (0, 10)])
        pivots = poly.ext.decompose(Point).drop_right(1).map(Pivot).to_list()
        valid_edges = [DirectEdge(p, np) for p, np in win_slice(pivots, win_size=2, tail_cycling=True)]
        closure = Closure(valid_edges)
        _ = Stretch([closure])

        divider = [LineString([(i, 0), (i, 10)]) for i in range(0, 110, 10)]
        result = closure.divided_by(divider)

        self.assertEqual(10, len(result))
        self.assertTrue(all(isinstance(item, Closure) for item in result))

        result.sort(key=lambda cls: cls.shape.centroid.x)
        for i, closure in enumerate(result):
            self.assertTrue(closure.shape.equals(box(i * 10, 0, i * 10 + 10, 10)))

    def test_divided_by_nothing(self):
        poly = box(0, 0, 1, 1)
        pivots = poly.ext.decompose(Point).drop_right(1).map(Pivot).to_list()
        valid_edges = [DirectEdge(p, np) for p, np in win_slice(pivots, win_size=2, tail_cycling=True)]
        closure = Closure(valid_edges)
        _ = Stretch([closure])

        divider_0 = None
        result = closure.divided_by(divider_0)
        self.assertEqual(result, [closure])

        divider_1 = []
        result = closure.divided_by(divider_1)
        self.assertEqual(result, [closure])

        divider_2 = LineString()
        result = closure.divided_by(divider_2)
        self.assertEqual(result, [closure])

    def test_divided_by_divider_cross_pivot(self):
        poly = box(0, 0, 4, 4)
        pivots = poly.ext.decompose(Point).drop_right(1).map(Pivot).to_list()
        valid_edges = [DirectEdge(p, np) for p, np in win_slice(pivots, win_size=2, tail_cycling=True)]
        closure = Closure(valid_edges)
        _ = Stretch([closure])

        divider = LineString([(0, 0), (4, 4)])
        result = closure.divided_by(divider)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].shape.area, 8)
        self.assertEqual(len(result[0].pivots), 3)
        self.assertEqual(len(result[0].edges), 3)
        self.assertEqual(len(result[0].stretch.pivots), 4)
        self.assertEqual(len(result[0].stretch.edges), 6)

    def test_union_simple_closure(self):
        poly_0 = box(0, 0, 2, 2)
        poly_1 = box(2, 0, 3, 1)
        goal_shape = Polygon([(0, 0), (3, 0), (3, 1), (2, 1), (2, 2), (0, 2), (0, 0)])
        stretch = StretchFactory().create([poly_0, poly_1])

        closure_0, closure_1 = stretch.closures
        union_closure = closure_0.union(closure_1)
        self.assertEqual(len(union_closure), 1)
        self.assertEqual(union_closure[0].stretch, stretch)
        self.assertTrue(goal_shape.equals(union_closure[0].shape))
        self.assertEqual(len(union_closure[0].edges), 7)
        self.assertEqual(len(union_closure[0].pivots), 7)

        self.assertEqual(len(stretch.closures), 1)
        self.assertEqual(len(stretch.pivots), 7)
        self.assertEqual(len(stretch.edges), 7)

    def test_union_complex_closure(self):
        poly_0 = Polygon([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (2, 2), (2, 3), (0, 3), (0, 0)])
        poly_1 = box(1, 1, 2, 2)
        goal_shape = box(0, 0, 2, 3)
        stretch = StretchFactory().create([poly_0, poly_1])

        closure_0, closure_1 = stretch.closures
        union_closure = closure_0.union(closure_1)
        self.assertEqual(len(union_closure), 1)
        self.assertEqual(union_closure[0].stretch, stretch)
        self.assertTrue(goal_shape.equals(union_closure[0].shape))
        self.assertEqual(len(union_closure[0].edges), 6)
        self.assertEqual(len(union_closure[0].pivots), 6)

        self.assertEqual(len(stretch.closures), 1)
        self.assertEqual(len(stretch.pivots), 6)
        self.assertEqual(len(stretch.edges), 6)

    def test_union_closures_not_intersects(self):
        poly_0 = box(0, 0, 1, 1)
        poly_1 = box(2, 2, 4, 4)

        stretch = StretchFactory().create([poly_0, poly_1])

        closure_0, closure_1 = stretch.closures
        union_closure = closure_0.union(closure_1)
        self.assertEqual(len(union_closure), 2)

        union_closure = sorted(union_closure, key=lambda c: c.shape.area)
        self.assertTrue(poly_0.equals(union_closure[0].shape))
        self.assertTrue(poly_1.equals(union_closure[1].shape))


class StretchTest(TestCase):
    def test_divided_with_simple_poly(self):
        poly = box(0, 0, 4, 4)
        stretch = StretchFactory().create(poly)
        divider = LineString([(1, 0), (1, 4)])

        self.assertEqual(1, len(stretch.closures))
        self.assertEqual(4, len(stretch.edges))
        self.assertEqual(4, len(stretch.pivots))

        stretch.divided_by(divider)

        self.assertEqual(len(stretch.pivots), 6)
        self.assertEqual(len(stretch.edges), 8)
        self.assertEqual(len(stretch.closures), 2)

        closures = sorted(stretch.closures, key=lambda cls: cls.shape.centroid.x)
        self.assertTrue(closures[1].shape.equals(box(1, 0, 4, 4)))
        self.assertTrue(closures[0].shape.equals(box(0, 0, 1, 4)))

    def test_divided_with_complex_poly(self):
        poly = Polygon([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (2, 2), (2, 3), (0, 3), (0, 0)])
        stretch = StretchFactory().create(poly)
        divider = LineString([(1, 0), (1, 4)])

        self.assertEqual(8, len(stretch.pivots))
        self.assertEqual(1, len(stretch.closures))
        self.assertEqual(8, len(stretch.edges))

        stretch.divided_by(divider)
        closures = sorted(stretch.closures, key=lambda cls: cls.shape.centroid.x)
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

        closures = stretch.divided_by(divider)
        self.assertEqual(len(stretch.pivots), 5)
        self.assertEqual(len(stretch.edges), 12)
        self.assertEqual(len(stretch.closures), 4)
        self.assertEqual(closures[0].shape.area, 4)
        self.assertEqual(closures[1].shape.area, 4)
        self.assertEqual(closures[2].shape.area, 4)
        self.assertEqual(closures[3].shape.area, 4)

    def test_divided_multi_polys_by_linestring(self):
        poly_0 = box(0, 0, 1, 1)
        poly_1 = box(1, 0, 2, 1)
        stretch = StretchFactory().create([poly_0, poly_1])

        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(6, len(stretch.pivots))
        self.assertEqual(8, len(stretch.edges))

        divider = LineString([(-1, 0.5), (3, 0.5)])
        stretch.divided_by(divider)

        self.assertEqual(4, len(stretch.closures))
        self.assertEqual(9, len(stretch.pivots))
        self.assertEqual(16, len(stretch.edges))

    def test_divided_by_many_lines(self):
        poly_0 = box(0, 0, 50, 20)
        poly_1 = box(50, 0, 100, 20)
        poly_2 = box(0, 20, 100, 40)
        lines = [LineString([(i, 0), (i, 40)]) for i in range(0, 110, 10)]
        stretch = StretchFactory().create([poly_0, poly_1, poly_2])
        self.assertEqual(3, len(stretch.closures))
        self.assertEqual(8, len(stretch.pivots))
        self.assertEqual(13, len(stretch.edges))

        stretch.divided_by(lines)
        self.assertEqual(20, len(stretch.closures))
        self.assertEqual(33, len(stretch.pivots))
        self.assertEqual(80, len(stretch.edges))

    def test_delete_closure(self):
        poly_0 = box(0, 0, 8, 8)
        poly_1 = box(8, 0, 16, 8)
        stretch = StretchFactory().create([poly_0, poly_1])

        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(6, len(stretch.pivots))
        self.assertEqual(8, len(stretch.edges))

        stretch.closures[0].delete()

        self.assertEqual(1, len(stretch.closures))
        self.assertEqual(4, len(stretch.pivots))
        self.assertEqual(4, len(stretch.edges))

        del stretch.closures[0]

        self.assertEqual(0, len(stretch.closures))
        self.assertEqual(0, len(stretch.pivots))
        self.assertEqual(0, len(stretch.edges))

    def test_append_closure(self):
        poly_0 = box(0, 0, 1, 1)
        stretch_0 = StretchFactory().create(poly_0)
        poly_1 = box(1, 0, 2, 2)
        stretch_1 = StretchFactory().create(poly_1)

        stretch_0.append(stretch_1.closures[0])
        self.assertEqual(len(stretch_0.closures), 2)
        self.assertEqual(len(stretch_0.pivots), 7)
        self.assertEqual(len(stretch_0.edges), 9)
        self.assertEqual(len(stretch_1.closures), 0)
        self.assertEqual(len(stretch_1.pivots), 0)
        self.assertEqual(len(stretch_1.edges), 0)
        self.assertEqual(stretch_0.closures[-1].pivots[-1].stretch, stretch_0)

        poly_2 = box(0, 1, 1, 2)
        stretch_2 = StretchFactory().create(poly_2)
        stretch_0.append(stretch_2.closures[0])
        self.assertEqual(len(stretch_0.closures), 3)
        self.assertEqual(len(stretch_0.pivots), 8)
        self.assertEqual(len(stretch_0.edges), 13)
        self.assertEqual(stretch_0.closures[-1].pivots[0].stretch, stretch_0)


class StretchFactorTest(TestCase):
    def test_reference_relationship(self):
        poly = box(0, 0, 1, 1)
        stretch = StretchFactory().create(poly)
        self.assertTrue(all(pivot.stretch is stretch for pivot in stretch.pivots))
        self.assertTrue(all(edge.stretch is stretch for edge in stretch.edges))
        self.assertTrue(all(closure.stretch is stretch for closure in stretch.closures))

    def test_stretch_created_by_single_poly(self):
        poly = box(0, 0, 1, 1)
        stretch = StretchFactory().create(poly)
        self.assertEqual(len(stretch.pivots), 4)
        self.assertEqual(len(stretch.edges), 4)
        self.assertEqual(len(stretch.closures), 1)
        self.assertEqual(stretch.closures[0].shape, poly)

    def test_stretch_created_by_single_multi_polygon(self):
        multi_poly = loads('MULTIPOLYGON (((-1 2, 0 2, 0 1, -1 1, -1 2)), ((0 2.5, 0.5 2.5, 0.5 2, 0 2, 0 2.5)))')
        stretch = StretchFactory().create(multi_poly)
        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(7, len(stretch.pivots))
        self.assertEqual(8, len(stretch.edges))

    def test_stretch_created_by_multi_polygons(self):
        pass

    def test_stretch_created_by_invalid_input(self):
        poly = box(0, 0, 0, 0)
        with self.assertRaises(ValueError):
            StretchFactory().create(poly)

        poly = Polygon()
        with self.assertRaises(ValueError):
            StretchFactory().create(poly)

        poly = Polygon(shell=((0, 0), (2, 0), (0, 2), (2, 2), (0, 0)),
                       holes=[((0.5, 0.5), (1, 0.5), (1, 1), (0.5, 1), (0.5, 0.5))])
        with self.assertRaises(ValueError):
            StretchFactory().create(poly)

    def test_stretch_created_by_simple_polys(self):
        polys = [
            box(0, 0, 1, 1),
            box(1, 0, 2, 2),
            box(0, 1, 1, 3)
        ]
        stretch = StretchFactory().create(polys)

        self.assertEqual(len(stretch.pivots), 9)
        self.assertEqual(len(stretch.edges), 14)
        self.assertEqual(len(stretch.closures), 3)
        self.assertEqual(len(stretch.closures[0]._edges), 4)
        self.assertEqual(len(stretch.closures[1]._edges), 5)
        self.assertEqual(len(stretch.closures[2]._edges), 5)
        self.assertTrue(stretch.closures[0].shape.equals(polys[0]))
        self.assertTrue(stretch.closures[1].shape.equals(polys[1]))
        self.assertTrue(stretch.closures[2].shape.equals(polys[2]))

    def test_stretch_created_by_2_boxes(self):
        poly_0 = box(0, 0, 1, 1)
        poly_1 = box(1, 0, 2, 1)
        stretch = StretchFactory().create([poly_0, poly_1])
        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(6, len(stretch.pivots))
        self.assertTrue(8, len(stretch.edges))

    def test_stretch_created_by_polys_with_eps(self):
        polys = [
            box(0, 0, 1, 1),
            box(1.1, 0, 2, 2),
            box(0.1, 1, 1, 3)
        ]
        stretch = StretchFactory(dist_tol=0.2).create(polys)

        self.assertEqual(len(stretch.pivots), 9)
        self.assertEqual(len(stretch.edges), 14)
        self.assertEqual(len(stretch.closures), 3)
        self.assertEqual(len(stretch.closures[0]._edges), 4)
        self.assertEqual(len(stretch.closures[1]._edges), 5)
        self.assertEqual(len(stretch.closures[2]._edges), 5)
        self.assertTrue(stretch.closures[0].shape.equals(polys[0]))
        self.assertTrue(stretch.closures[1].shape.equals(Polygon([(1, 0), (2, 0), (2, 2), (1.1, 2), (1, 1)])))
        self.assertTrue(stretch.closures[2].shape.equals(Polygon([(0, 1), (1, 1), (1.1, 2), (1, 3), (0.1, 3)])))

    def test_stretch_created_by_overlapping_polys(self):
        polys = [
            loads('POLYGON ((-1 2, -1 1, 0 1, 0 2, -1 2))'),
            loads('POLYGON ((0 1.5, -0.2 0, 1 0, 1 1.5, 0 1.5))')]

        stretch = StretchFactory(dist_tol=0.2).create(polys)
        self.assertEqual(2, len(stretch.closures))
        self.assertEqual(8, len(stretch.pivots))
        self.assertEqual(10, len(stretch.edges))
        self.assertEqual(5, len(stretch.closures[0]._edges))
        self.assertEqual(5, len(stretch.closures[1]._edges))
        self.assertTrue(stretch.closures[0].shape.equals(polys[0]))
        self.assertTrue(stretch.closures[1].shape.equals(Polygon([(-0.2, 0), (1, 0), (1, 1.5), (0, 1.5), (0, 1)])))

    def test_stretch_created_by_polys_that_created_by_difference(self):
        poly = loads('POLYGON ((0 3, 3 3, 3 0, 0 0, 0 3))')
        multi_line = loads('MULTILINESTRING ((1 3.5, 1 -0.6), (-0.5 1.5, 3.5 1.5))')
        result = poly.ext.difference(multi_line, component_buffer=1e-12)

        stretch = StretchFactory(dist_tol=1e-6).create(result)
        self.assertEqual(4, len(stretch.closures))

    def test_stretch_created_by_dividing_polys(self):
        pass
