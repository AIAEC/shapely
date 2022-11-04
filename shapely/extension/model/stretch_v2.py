from copy import deepcopy
from dataclasses import dataclass, field
from functools import partial, cached_property
from itertools import combinations
from operator import truth, attrgetter
from typing import Union, List, Optional, Set, Sequence
from uuid import uuid4
from weakref import ref, ReferenceType

from functional import seq
from toolz import concat

from shapely.extension.constant import MATH_EPS
from shapely.extension.geometry import StraightSegment
from shapely.extension.model import Coord, Vector, Angle
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter, lmap, separate
from shapely.extension.util.iter_util import win_slice, first
from shapely.geometry import Point, Polygon, MultiPolygon, LineString
from shapely.geometry.base import BaseGeometry


class Pivot:
    def __init__(self, origin: Union[Coord, Point], stretch: 'Stretch'):
        try:
            self._origin = Point(origin)
        except Exception:
            raise TypeError(f'given origin cannot form a point, given {origin}')

        if not self._origin.is_valid or self._origin.is_empty:
            raise ValueError(f'origin is invalid point, given {origin}')

        self.in_edges = []
        self.out_edges = []
        self._stretch: ReferenceType['Stretch'] = ref(stretch)
        self.cargo = {}
        self.id = uuid4()

    def __hash__(self):
        return hash(('pivot', self.id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return f'Pivot({self.shape.x}, {self.shape.y})@{str(self.id)[:4]}'

    @property
    def stretch(self) -> 'Stretch':
        return self._stretch()

    @property
    def shape(self) -> Point:
        return self._origin

    @property
    def valid(self) -> bool:
        return len(self.in_edges) == len(self.out_edges)

    @property
    def dangling(self) -> bool:
        return len(self.in_edges) + len(self.out_edges) == 0

    def move_to(self, target: Union[Point, Coord]) -> None:
        try:
            target = Point(target)
        except Exception:
            raise TypeError(f'target cannot form a point, given {target}')
        self._origin = target

    def move_by(self, direct: Vector) -> None:
        if not isinstance(direct, Vector):
            raise TypeError(f'direct must be vector, given {direct}')

        self._origin = direct.apply(self._origin)

    def move_along(self):
        pass


class DirectEdge:
    def __init__(self, from_pivot: Pivot, to_pivot: Pivot, stretch: 'Stretch'):
        self.from_pivot = from_pivot
        self.to_pivot = to_pivot
        self._stretch: ReferenceType['Stretch'] = ref(stretch)
        self.cargo = {}

        if self not in self.from_pivot.out_edges:
            self.from_pivot.out_edges.append(self)
        if self not in self.to_pivot.in_edges:
            self.to_pivot.in_edges.append(self)

    def __hash__(self):
        return hash((hash(self.from_pivot), hash(self.to_pivot)))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return f'Edge(({self.from_pivot})->({self.to_pivot}))'

    @property
    def reverse(self) -> Optional['DirectEdge']:
        return first(lambda edge: edge.from_pivot == self.to_pivot and edge.to_pivot == self.from_pivot,
                     iter=self.stretch.edges,
                     default=None)

    @property
    def stretch(self) -> 'Stretch':
        return self._stretch()

    @property
    def shape(self) -> StraightSegment:
        return StraightSegment([self.from_pivot.shape, self.to_pivot.shape])

    def offset(self, strategy) -> None:
        pass

    def expand(self, point: Point, endpoint_dist_tol: float = MATH_EPS) -> Pivot:
        reverse_existed = bool(self.reverse)
        closest_end_pivot = min([self.from_pivot, self.to_pivot], key=lambda pivot: pivot.shape.distance(point))
        if closest_end_pivot.shape.distance(point) <= endpoint_dist_tol:
            # don't expand if given point is too close to the end pivots
            return closest_end_pivot

        # create insertion pivot
        insert_pivot = Pivot(point, self.stretch)

        # delete edge ref in pivot
        self.from_pivot.out_edges.remove(self)
        self.to_pivot.in_edges.remove(self)

        # delete edge record in stretch and add 2 new edges
        self.stretch.edges.append(DirectEdge(from_pivot=self.from_pivot, to_pivot=insert_pivot, stretch=self.stretch))
        self.stretch.edges.append(DirectEdge(from_pivot=insert_pivot, to_pivot=self.to_pivot, stretch=self.stretch))
        self.stretch.edges.remove(self)

        if reverse_existed:
            # delete reverse edge ref in pivot
            reverse_edge = self.reverse
            self.from_pivot.in_edges.remove(reverse_edge)
            self.to_pivot.out_edges.remove(reverse_edge)

            # delete reverse edge record in stretch and add 2 new edges
            self.stretch.edges.append(
                DirectEdge(from_pivot=insert_pivot, to_pivot=self.from_pivot, stretch=self.stretch))
            self.stretch.edges.append(DirectEdge(from_pivot=self.to_pivot, to_pivot=insert_pivot, stretch=self.stretch))
            self.stretch.edges.remove(reverse_edge)

        # add new pivot ot stretch
        self.stretch.pivots.append(insert_pivot)

        return insert_pivot


class DirectEdgeView(DirectEdge):
    """
    View for direct edge, creating DirectEdgeView will not change the data inside stretch
    """

    def __init__(self, from_pivot: Pivot, to_pivot: Pivot, stretch: 'Stretch'):
        self.from_pivot = deepcopy(from_pivot)
        self.to_pivot = deepcopy(to_pivot)
        self._stretch: ReferenceType['Stretch'] = ref(stretch)
        self.cargo = {}

    @property
    def reverse(self) -> 'DirectEdgeView':
        return DirectEdgeView(from_pivot=self.to_pivot, to_pivot=self.from_pivot, stretch=self.stretch)


@dataclass(frozen=True)
class ClosureView:
    pivots: List[Pivot] = field(default_factory=list)  # no duplicated tail pivot

    @cached_property
    def edges(self) -> List[DirectEdgeView]:
        return [DirectEdgeView(from_pivot, to_pivot, from_pivot.stretch)
                for from_pivot, to_pivot in win_slice(self.pivots, win_size=2, tail_cycling=True)]

    @cached_property
    def shape(self) -> Polygon:
        return Polygon([pivot.shape for pivot in self.pivots])

    def shared_edges(self, closure: 'ClosureView') -> List[DirectEdgeView]:
        edge_set: Set[DirectEdgeView] = set(self.edges)
        return lfilter(lambda edge: edge.reverse in edge_set, closure.edges)


class ClosureSnapshot:
    def __init__(self, closures: List[ClosureView]):
        self.closures: List[ClosureView] = closures

    @staticmethod
    def next_edge(edge: DirectEdge) -> Optional[DirectEdge]:
        def candidate_edge(other_edge: DirectEdge) -> bool:
            return not ((edge.from_pivot == other_edge.from_pivot and edge.to_pivot == other_edge.to_pivot)
                        or (edge.from_pivot == other_edge.to_pivot and edge.to_pivot == other_edge.from_pivot))

        out_edges = lfilter(candidate_edge, edge.to_pivot.out_edges)
        if not out_edges:
            return None

        invert_edge_angle: Angle = edge.shape.ext.inverse().ext.angle()

        def ccw_rotating_angle_to_inversion_of_given_edge(other_edge: DirectEdge):
            return other_edge.shape.ext.angle().rotating_angle(invert_edge_angle, direct='ccw')

        return min(out_edges, key=ccw_rotating_angle_to_inversion_of_given_edge)

    @staticmethod
    def find_edge_ring(edge: DirectEdge) -> List[DirectEdge]:
        # TODO: explain the algorithm
        ring_edges: List[DirectEdge] = [edge]
        seen = set(ring_edges)
        while (next_edge := ClosureSnapshot.next_edge(edge)) and (next_edge not in seen):
            ring_edges.append(next_edge)
            edge = next_edge

        return ring_edges

    @classmethod
    def create_from(cls, stretch):
        edge_set: Set[DirectEdge] = set(stretch.edges)

        ring_edge_groups: List[List[DirectEdge]] = []
        guard = len(stretch.edges)
        while edge_set and guard > 0:
            guard -= 1
            starting_edge = edge_set.pop()

            edges = cls.find_edge_ring(starting_edge)
            ring_edge_groups.append(edges)

            edge_set.difference_update(set(edges))

        def ring_edge_to_closure(ring_edges: List[DirectEdge]) -> Optional[ClosureView]:
            if not ring_edges:
                return None

            pivots: List[Pivot] = [ring_edges[0].from_pivot]
            for edge in ring_edges:
                if edge.from_pivot != pivots[-1]:  # cannot form a ring
                    return None
                pivots.append(edge.to_pivot)

            if pivots[0] != pivots[-1]:
                return None

            return ClosureView(pivots[:-1])  # don't include duplicate tail pivot

        closures: List[ClosureView] = (seq(ring_edge_groups)
                                       .map(ring_edge_to_closure)
                                       .filter(truth)
                                       .to_list())

        return ClosureSnapshot(closures)

    @property
    def occupation(self) -> MultiPolygon:
        return MultiPolygon(lmap(attrgetter('shape'), self.closures))

    def query_closures(self, geom: BaseGeometry) -> List[ClosureView]:
        return lfilter(lambda closure: closure.shape.intersects(geom), self.closures)


class Stretch:
    def __init__(self, pivots: List[Pivot], edges: List[DirectEdge]):
        self.pivots: List[pivots] = pivots
        self.edges: List[DirectEdge] = edges
        self.id = uuid4()

    def closure_snapshot(self) -> ClosureSnapshot:
        return ClosureSnapshot.create_from(self)

    def query_pivots(self, geom: BaseGeometry, buffer: float = 0) -> List[Pivot]:
        if buffer != 0:
            geom = geom.buffer(buffer)
        return lfilter(lambda pivot: geom.intersects(pivot.shape), self.pivots)

    def query_edges(self, geom: BaseGeometry, buffer: float = 0) -> List[DirectEdge]:
        if buffer != 0:
            geom = geom.buffer(buffer)
        return lfilter(lambda edge: geom.intersects(edge.shape), self.edges)

    def remove_dangling_pivots(self) -> None:
        self.pivots = lfilter(lambda pivot: not pivot.dangling, self.pivots)

    def remove_dangling_edges(self) -> None:
        valid_edges: Set[DirectEdgeView] = set(concat(closure.edges for closure in self.closure_snapshot().closures))
        self.edges = lfilter(lambda edge: edge in valid_edges, self.edges)

    def _remove_edges(self, edges: Sequence[DirectEdge], delete_reverse: bool = False) -> None:
        # only used as internal method, don't use it publicly
        if delete_reverse:
            deleting_edge_views: Set[DirectEdge] = set(concat([(e, e.reverse) for e in edges]))
        else:
            deleting_edge_views: Set[DirectEdge] = set(edges)

        deleting_edges, self.edges = separate(lambda edge: edge in deleting_edge_views, self.edges)

        for deleting_edge in deleting_edges:
            deleting_edge.from_pivot.out_edges.remove(deleting_edge)
            deleting_edge.to_pivot.in_edges.remove(deleting_edge)

        self.remove_dangling_pivots()

    def remove_closure(self, closure_copy: ClosureView) -> None:
        self._remove_edges(closure_copy.edges, delete_reverse=False)

    def union_closures(self, closure_copies: List[ClosureView]) -> None:
        if len(closure_copies) < 2:
            return

        for closure_copy0, closure_copy1 in combinations(closure_copies, 2):
            self._remove_edges(closure_copy0.shared_edges(closure_copy1), delete_reverse=True)

    def _query_attachable_pivot(self, point: Point, dist_tol: float = MATH_EPS) -> Pivot:
        pivots = self.query_pivots(geom=point, buffer=dist_tol)
        return min(pivots, key=lambda pivot: pivot.shape.distance(point), default=None)

    def _query_attachable_edge(self, point: Point, dist_tol: float = MATH_EPS) -> DirectEdge:
        edges = self.query_edges(geom=point, buffer=dist_tol)
        return min(edges, key=lambda edge: edge.shape.distance(point), default=None)

    def add_pivot(self, point: Point,
                  reuse_existing: bool = True,
                  attach_to_nearest_edge: bool = True,
                  dist_tol: float = MATH_EPS) -> Pivot:
        if not isinstance(point, Point) or not point.is_valid or point.is_empty:
            raise ValueError(f'expect valid point, given {point}')

        if reuse_existing:
            if existed_pivot := self._query_attachable_pivot(point, dist_tol):
                return existed_pivot

            if attach_to_nearest_edge and (existed_edge := self._query_attachable_edge(point, dist_tol)):
                return existed_edge.expand(point, endpoint_dist_tol=dist_tol)

        new_pivot = Pivot(point, stretch=self)
        self.pivots.append(new_pivot)

        return new_pivot

    def add_closure(self, polygon: Polygon,
                    reuse_existing: bool = True,
                    attach_to_nearest_edge: bool = True,
                    dist_tol: float = MATH_EPS) -> List[Pivot]:
        add_pivot = partial(self.add_pivot,
                            reuse_existing=reuse_existing,
                            attach_to_nearest_edge=attach_to_nearest_edge,
                            dist_tol=dist_tol)

        pivots: List[Pivot] = (polygon.exterior
                               .ext.ccw()
                               .ext.decompose(Point)
                               .map(lambda pt: add_pivot(point=pt))
                               .to_list())

        for from_pivot, to_pivot in win_slice(pivots, win_size=2, tail_cycling=True):
            edge = DirectEdge(from_pivot, to_pivot, stretch=self)
            if edge not in self.edges:
                self.edges.append(edge)

        return pivots

    def split_by(self, line: LineString, dist_tol: float = MATH_EPS) -> bool:
        from shapely.extension.util.offset import self_intersection

        lines_inside: List[LineString] = (self.closure_snapshot().occupation
                                          .intersection(line)
                                          .ext.decompose(LineString)
                                          .filter(truth)
                                          .filter_not(self_intersection)
                                          .to_list())

        def find_attaching_edge(point: Point) -> Optional[DirectEdge]:
            return min(self.query_edges(point, buffer=dist_tol),
                       key=lambda edge: edge.shape.distance(point),
                       default=None)

        add_pivot = partial(self.add_pivot,
                            reuse_existing=True,
                            attach_to_nearest_edge=True,
                            dist_tol=dist_tol)

        changed: bool = False

        for line_inside in lines_inside:
            line_inside = line_inside.simplify(0)
            start_point = line_inside.ext.start()
            end_point = line_inside.ext.end()

            start_inserting_edge = find_attaching_edge(start_point)
            end_inserting_edge = find_attaching_edge(end_point)
            if not (start_inserting_edge and end_inserting_edge):
                continue  # just ignore this invalid line

            # add pivots without duplicate
            new_pivots: List[Pivot] = lmap(add_pivot, line_inside.ext.decompose(Point).to_list())

            # add edges
            new_edges: Set[DirectEdge] = set()
            for _from_pivot, _to_pivot in win_slice(new_pivots, win_size=2):
                new_edges.add(DirectEdge(_from_pivot, _to_pivot, stretch=self))
                new_edges.add(DirectEdge(_to_pivot, _from_pivot, stretch=self))

            # remove possible duplicated edges
            new_edges.difference_update(set(self.edges))
            self.edges.extend(new_edges)

            changed |= bool(new_edges)

        # when splitter exactly touches the closure boundary, it will create dangling edges, clean these edges here
        self.remove_dangling_edges()

        return changed


class StretchFactory:
    def __init__(self, dist_tol: float = MATH_EPS):
        self._dist_tol = dist_tol

    def create(self, geom_or_geoms: Union[BaseGeometry]) -> Stretch:
        stretch = Stretch([], [])

        polys = (flatten(geom_or_geoms)
                 .filter(lambda geom: isinstance(geom, Polygon))
                 .filter(truth)
                 .to_list())

        for poly in polys:
            stretch.add_closure(poly)

        return stretch
