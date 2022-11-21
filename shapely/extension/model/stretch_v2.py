"""
Stretch is a set of model that used to represent polygons with shared edge
Core Concepts:
1. Pivot: the actual "point" of each polygon
2. DirectEdge: the "edge" of each polygon, notice that left side of direct edge is the inner side of polygon
3. ClosureView: the polygon that closed by direct edges, which in stretch model, is an object only derived from edges
"""

import pickle
from abc import ABC, abstractmethod
from contextlib import suppress
from copy import deepcopy
from dataclasses import dataclass, field
from functools import partial, cached_property
from itertools import combinations, product
from operator import truth, attrgetter
from typing import Union, List, Optional, Set, Sequence, Literal, Iterable, Dict, Tuple, Callable
from uuid import uuid4
from weakref import ref, ReferenceType

from toolz import concat

from shapely.extension.constant import MATH_EPS, ANGLE_AROUND_EPS
from shapely.extension.geometry import StraightSegment
from shapely.extension.model import Coord, Vector, Angle
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter, lmap, separate
from shapely.extension.util.iter_util import win_slice, first
from shapely.extension.util.ordered_set import OrderedSet
from shapely.geometry import Point, Polygon, MultiPolygon, LineString, MultiLineString, GeometryCollection
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

CargoInheritStrategy = Callable[[dict], dict]
default_cargo_inherit_strategy: CargoInheritStrategy = lambda cargo: deepcopy(cargo)
CargoUnionStrategy = Callable[[dict, dict], dict]
default_cargo_union_strategy: CargoUnionStrategy = lambda cargo0, cargo1: deepcopy(cargo0)


class Pivot:
    """
    The representative point in stretch model
    """

    def __init__(self, origin: Union[Coord, Point],
                 stretch: 'Stretch',
                 cargo: Optional[dict] = None):
        try:
            self._origin = Point(origin)
        except Exception:
            raise TypeError(f'given origin cannot form a point, given {origin}')

        if not self._origin.is_valid or self._origin.is_empty:
            raise ValueError(f'origin is invalid point, given {origin}')

        self.in_edges: List[DirectEdge] = []
        self.out_edges: List[DirectEdge] = []
        self._stretch: 'Stretch' = stretch
        self.cargo = cargo or {}
        self.id = uuid4()

    def __hash__(self):
        return hash(('pivot', self.id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return f'Pivot({self.shape.x}, {self.shape.y})@{str(self.id)[:4]}'

    @property
    def stretch(self) -> 'Stretch':
        return self._stretch

    @property
    def shape(self) -> Point:
        return self._origin

    @property
    def valid(self) -> bool:
        return len(self.in_edges) == len(self.out_edges)

    @property
    def dangling(self) -> bool:
        return len(self.in_edges) + len(self.out_edges) < 2

    def distance(self, point: Union[Point, 'Pivot']) -> float:
        point = point.shape if isinstance(point, Pivot) else point
        return self.shape.distance(point)

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


class DirectEdge:
    """
    The representative linestring in stretch model
    """

    def __init__(self, from_pivot: Pivot,
                 to_pivot: Pivot,
                 stretch: 'Stretch',
                 cargo: Optional[dict] = None):

        self._from_pivot = ref(from_pivot)
        self._to_pivot = ref(to_pivot)
        self._stretch: 'Stretch' = stretch
        self.cargo = cargo or {}

        if self not in from_pivot.out_edges:
            from_pivot.out_edges.append(self)
        if self not in to_pivot.in_edges:
            to_pivot.in_edges.append(self)

    @property
    def from_pivot(self):
        # pivot owns edges, thus edge weak ref to pivot to prevent recursive ref
        # especially when we use deepcopy
        return self._from_pivot()

    @property
    def to_pivot(self):
        # pivot owns edges, thus edge weak ref to pivot to prevent recursive ref
        # especially when we use deepcopy
        return self._to_pivot()

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

    def is_reversed(self, edge: 'DirectEdge') -> bool:
        return self.from_pivot == edge.to_pivot and self.to_pivot == edge.from_pivot

    @property
    def stretch(self) -> 'Stretch':
        return self._stretch

    @property
    def shape(self) -> StraightSegment:
        return StraightSegment([self.from_pivot.shape, self.to_pivot.shape])

    def _is_valid_neighbor(self, other_edge: 'DirectEdge') -> bool:
        try:
            return not (self == other_edge
                        or self.is_reversed(other_edge)
                        or not other_edge.shape.is_valid
                        or isinstance(other_edge, DirectEdgeView))
        except AttributeError:
            return False

    @property
    def next(self) -> Optional['DirectEdge']:
        """
        Returns
        -------
        the next DirectEdge of current edge of same closure
        """
        if not self.shape.is_valid:
            return None

        out_edges = lfilter(self._is_valid_neighbor, self.to_pivot.out_edges)

        if len(out_edges) == 1:  # for speed up
            return out_edges[0]

        invert_edge_angle: Angle = self.shape.ext.inverse().ext.angle()

        def other_ccw_rotating_angle_to_inversion_of_given_edge(other_edge: DirectEdge):
            return other_edge.shape.ext.angle().rotating_angle(invert_edge_angle, direct='ccw')

        return min(out_edges, key=other_ccw_rotating_angle_to_inversion_of_given_edge, default=None)

    @property
    def previous(self) -> Optional['DirectEdge']:
        """
        Returns
        -------
        the previous DirectEdge of current edge of same closure
        """
        if not self.shape.is_valid:
            return None

        in_edges = lfilter(self._is_valid_neighbor, self.from_pivot.in_edges)

        if len(in_edges) == 1:  # for speed up
            return in_edges[0]

        self_angle: Angle = self.shape.ext.angle()

        def self_ccw_rotating_angle_to_inversion_of_other_edge(other_edge: DirectEdge):
            return self_angle.rotating_angle(other_edge.shape.ext.inverse().ext.angle(), direct='ccw')

        return min(in_edges, key=self_ccw_rotating_angle_to_inversion_of_other_edge, default=None)

    @staticmethod
    def consecutive_edges(edge: 'DirectEdge') -> List['DirectEdge']:
        """
        Parameters
        ----------
        edge

        Returns
        -------
        the serial of next edges in consecutive orders of the same closure
        """
        # TODO: explain the algorithm
        ring_edges: List[DirectEdge] = [edge]
        seen = set(ring_edges)
        while (next_edge := edge.next) and (next_edge not in seen):
            seen.add(next_edge)  # sanity guard
            ring_edges.append(next_edge)
            edge = next_edge

        return ring_edges

    @property
    def consecutive(self) -> List['DirectEdge']:
        return DirectEdge.consecutive_edges(self)

    @property
    def closure(self) -> Optional['ClosureView']:
        return ClosureView.create_from(self.consecutive)

    def offset(self, dist: float,
               side: Literal['left', 'right'],
               edge_offset_strategy_clz: type,
               attaching_dist_tol: float = MATH_EPS,
               cargo_inherit_strategy: CargoInheritStrategy = default_cargo_inherit_strategy) -> 'DirectEdge':

        edge_vec = Vector.from_endpoints_of(self.shape)
        if side == 'left':
            offset_vec = edge_vec.ccw_perpendicular.unit(dist)
        else:
            offset_vec = edge_vec.cw_perpendicular.unit(dist)

        new_edge: DirectEdge = edge_offset_strategy_clz(
            edge=self,
            offset_vector=offset_vec,
            attaching_dist_tol=attaching_dist_tol,
            edge_cargo_inherit_strategy=cargo_inherit_strategy,
            pivot_cargo_inherit_strategy=cargo_inherit_strategy).do()

        return new_edge

    def expand(self, point: Point,
               endpoint_dist_tol: float = MATH_EPS,
               pivot_cargo: Optional[dict] = None,
               cargo_inherit_strategy: CargoInheritStrategy = default_cargo_inherit_strategy) -> Pivot:
        reverse_existed = bool(self.reverse)
        closest_end_pivot = min([self.from_pivot, self.to_pivot], key=lambda pivot: pivot.distance(point))
        pivot_cargo = deepcopy(pivot_cargo) or {}
        if closest_end_pivot.distance(point) <= endpoint_dist_tol:
            # don't expand if given point is too close to the end pivots
            closest_end_pivot.cargo = pivot_cargo
            return closest_end_pivot

        # create insertion pivot
        insert_pivot = Pivot(point, self.stretch, cargo=pivot_cargo)

        # delete edge ref in pivot
        self.from_pivot.out_edges.remove(self)
        self.to_pivot.in_edges.remove(self)

        # delete edge record in stretch and add 2 new edges
        self.stretch.edges.append(DirectEdge(from_pivot=self.from_pivot,
                                             to_pivot=insert_pivot,
                                             stretch=self.stretch,
                                             cargo=cargo_inherit_strategy(self.cargo)))
        self.stretch.edges.append(DirectEdge(from_pivot=insert_pivot,
                                             to_pivot=self.to_pivot,
                                             stretch=self.stretch,
                                             cargo=cargo_inherit_strategy(self.cargo)))
        self.stretch.edges.remove(self)

        if reverse_existed:
            # delete reverse edge ref in pivot
            reverse_edge = self.reverse
            self.from_pivot.in_edges.remove(reverse_edge)
            self.to_pivot.out_edges.remove(reverse_edge)

            # delete reverse edge record in stretch and add 2 new edges
            self.stretch.edges.append(DirectEdge(from_pivot=insert_pivot,
                                                 to_pivot=self.from_pivot,
                                                 stretch=self.stretch,
                                                 cargo=cargo_inherit_strategy(reverse_edge.cargo)))
            self.stretch.edges.append(DirectEdge(from_pivot=self.to_pivot,
                                                 to_pivot=insert_pivot,
                                                 stretch=self.stretch,
                                                 cargo=cargo_inherit_strategy(reverse_edge.cargo)))
            self.stretch.edges.remove(reverse_edge)

        # add new pivot ot stretch
        self.stretch.pivots.append(insert_pivot)

        return insert_pivot

    def sub_edge(self, overlapping_geom: BaseGeometry,
                 buffer: float = 0,
                 endpoint_dist_tol: float = MATH_EPS,
                 pivot_cargo: Optional[dict] = None,
                 cargo_inherit_strategy: CargoInheritStrategy = default_cargo_inherit_strategy,
                 ) -> Optional['DirectEdge']:
        overlapping_segments: List[LineString] = (overlapping_geom.buffer(buffer)
                                                  .intersection(self.shape)
                                                  .ext.decompose(StraightSegment)
                                                  .to_list())
        segment = max(overlapping_segments, key=attrgetter('length'), default=None)
        if not segment:
            return None

        return self._sub_edge_by_points(start_point=segment.ext.start(),
                                        end_point=segment.ext.end(),
                                        endpoint_dist_tol=endpoint_dist_tol,
                                        pivot_cargo=pivot_cargo or {},
                                        cargo_inherit_strategy=cargo_inherit_strategy)

    def _sub_edge_by_points(self, start_point: Point,
                            end_point: Point,
                            endpoint_dist_tol: float = MATH_EPS,
                            pivot_cargo: Optional[dict] = None,
                            cargo_inherit_strategy: CargoInheritStrategy = default_cargo_inherit_strategy,
                            ) -> 'DirectEdge':
        def add_pivot(point) -> Pivot:
            if pivot := first(lambda pivot: pivot.distance(point) < endpoint_dist_tol,
                              [self.from_pivot, self.to_pivot]):
                return pivot
            assert not self.stretch.query_pivots(point, buffer=endpoint_dist_tol), \
                'new pivot should not overlap with existed'
            pivot = Pivot(point, stretch=self.stretch, cargo=deepcopy(pivot_cargo) or {})
            self.stretch.pivots.append(pivot)
            return pivot

        reverse_existed = bool(self.reverse)
        new_pivots = [add_pivot(start_point), add_pivot(end_point)]
        new_pivots.sort(key=lambda pivot: self.shape.project(pivot.shape))

        # delete edge ref in pivot
        self.from_pivot.out_edges.remove(self)
        self.to_pivot.in_edges.remove(self)

        pivots_on_line = [self.from_pivot, new_pivots[0], new_pivots[1], self.to_pivot]
        # delete edge record in stretch and add 3 new edges
        for from_pivot, to_pivot in win_slice(pivots_on_line, win_size=2):
            if from_pivot != to_pivot:
                self.stretch.edges.append(DirectEdge(from_pivot=from_pivot,
                                                     to_pivot=to_pivot,
                                                     stretch=self.stretch,
                                                     cargo=cargo_inherit_strategy(self.cargo)))

        self.stretch.edges.remove(self)

        if reverse_existed:
            # delete reverse edge ref in pivot
            reverse_edge = self.reverse
            self.from_pivot.in_edges.remove(reverse_edge)
            self.to_pivot.out_edges.remove(reverse_edge)

            # delete edge record in stretch and add 3 new edges
            for to_pivot, from_pivot in win_slice(pivots_on_line, win_size=2):
                if from_pivot != to_pivot:
                    self.stretch.edges.append(DirectEdge(from_pivot=from_pivot,
                                                         to_pivot=to_pivot,
                                                         stretch=self.stretch,
                                                         cargo=cargo_inherit_strategy(reverse_edge.cargo)))

            self.stretch.edges.remove(reverse_edge)

        return first(lambda edge: edge.from_pivot == new_pivots[0] and edge.to_pivot == new_pivots[1],
                     self.stretch.edges)


class DirectEdgeView(DirectEdge):
    """
    View object for direct edge, creating DirectEdgeView will not change the data inside stretch
    """

    def __init__(self, from_pivot: Pivot, to_pivot: Pivot, stretch: 'Stretch'):
        # Don't use its super(DirectEdge)'s __init__, because it will add self to its from and to pivots
        self._from_pivot = ref(from_pivot)
        self._to_pivot = ref(to_pivot)
        self._stretch: ReferenceType['Stretch'] = ref(stretch)
        self.cargo = {}

    @property
    def stretch(self) -> 'Stretch':
        return self._stretch()

    @property
    def reverse(self) -> 'DirectEdgeView':
        return DirectEdgeView(from_pivot=self.to_pivot, to_pivot=self.from_pivot, stretch=self.stretch)


@dataclass(frozen=True)
class ClosureView:
    """
    The representative polygon in stretch model
    """
    pivots: List[Pivot] = field(default_factory=list)  # no duplicated tail pivot

    def __bool__(self):
        try:
            return self.shape.is_valid
        except ValueError:
            return False

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

    @classmethod
    def create_from(cls, consecutive_edges: List[DirectEdge]) -> Optional['ClosureView']:
        if not consecutive_edges or consecutive_edges[0].from_pivot != consecutive_edges[-1].to_pivot:
            return None

        pivots: List[Pivot] = [consecutive_edges[0].from_pivot]
        for edge in consecutive_edges:
            if edge.from_pivot != pivots[-1]:  # cannot form a ring
                return None
            pivots.append(edge.to_pivot)

        return cls(pivots[:-1])  # don't include duplicate tail pivot


@dataclass(frozen=True)
class ClosureSnapshot:
    """
    The closure view set
    """
    closures: List[ClosureView] = field()

    @classmethod
    def create_from(cls, stretch):
        edge_set: OrderedSet = OrderedSet(stretch.edges)

        closures: List[ClosureView] = []

        guard = len(stretch.edges)
        while edge_set and guard > 0:
            guard -= 1
            starting_edge = edge_set.pop()
            assert isinstance(starting_edge, DirectEdge)

            edges: List[DirectEdge] = starting_edge.consecutive
            if not edges or edges[0].from_pivot != edges[-1].to_pivot:
                continue  # starting_edge's consecutive edges cannot form closure, just ignore it

            edge_set.difference_update(edges)
            if closure := ClosureView.create_from(edges):
                closures.append(closure)

        return ClosureSnapshot(closures)

    @property
    def occupation(self) -> MultiPolygon:
        return MultiPolygon(lmap(attrgetter('shape'), self.closures))

    def query_closures(self, geom: BaseGeometry) -> List[ClosureView]:
        return lfilter(lambda closure: closure.shape.intersects(geom), self.closures)


class Stretch:
    """
    The core model that hold every pivots and edges
    """

    def __init__(self, pivots: List[Pivot], edges: List[DirectEdge]):
        self.pivots: List[Pivot] = pivots
        self.edges: List[DirectEdge] = edges
        self.id = uuid4()

    def dump(self, fp, with_cargo: bool = True):
        if with_cargo:
            data = {'pivots': {pivot.id: (pivot.shape, pivot.cargo) for pivot in self.pivots},
                    'edges': [(edge.from_pivot.id, edge.to_pivot.id, edge.cargo) for edge in self.edges]}
        else:
            data = {'pivots': {pivot.id: pivot.shape for pivot in self.pivots},
                    'edges': [(edge.from_pivot.id, edge.to_pivot.id) for edge in self.edges]}

        pickle.dump(data, fp)

    @classmethod
    def load(cls, fp, with_cargo: bool = True):
        data = pickle.load(fp)
        point_dict: Dict[str, Tuple[Point, Optional[dict]]] = data['pivots']
        edge_info_tuples: List[Tuple[str, str, Optional[dict]]] = data['edges']

        stretch = cls([], [])
        pivot_dict: Dict[str, Pivot] = {}
        for id_, point_info in point_dict.items():
            if with_cargo:
                point, cargo = point_info
                pivot = Pivot(origin=point, stretch=stretch, cargo=cargo)
            else:
                assert isinstance(point_info, Point)
                pivot = Pivot(origin=point_info, stretch=stretch)
            pivot_dict[id_] = pivot

        for edge_info in edge_info_tuples:
            if with_cargo:
                from_pivot_id, to_pivot_id, edge_cargo = edge_info
            else:
                from_pivot_id, to_pivot_id, *_ = edge_info
                edge_cargo = {}

            from_pivot = pivot_dict[from_pivot_id]
            to_pivot = pivot_dict[to_pivot_id]
            stretch.edges.append(DirectEdge(from_pivot=from_pivot,
                                            to_pivot=to_pivot,
                                            stretch=stretch,
                                            cargo=edge_cargo))

        stretch.pivots = list(pivot_dict.values())

        return stretch

    def closure_snapshot(self) -> ClosureSnapshot:
        return ClosureSnapshot.create_from(self)

    def static_closure_snapshot(self) -> ClosureSnapshot:
        return ClosureSnapshot.create_from(deepcopy(self))

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

    def _force_remove_pivot(self, pivot: Pivot):
        # do not use this method publicly, this method is designed to be used as private method
        self._force_remove_edges([*pivot.in_edges, *pivot.out_edges], delete_reverse=True, clean_dangling=False)
        with suppress(ValueError):
            self.pivots.remove(pivot)

    def _remove_back_turning_edge(self) -> None:
        def removable_pivot(pivot: Pivot) -> bool:
            return len(pivot.in_edges) == len(pivot.out_edges) == 1 and pivot.in_edges[0].is_reversed(
                pivot.out_edges[0])

        def recursive_removable_candidate(pivot: Pivot) -> Optional[Pivot]:
            if len(pivot.in_edges) != 1:
                return None

            # removable pivot should only have 1 in-edge
            return pivot.in_edges[0].from_pivot

        removing_candidates: List[Pivot] = lfilter(removable_pivot, self.pivots)
        while removing_candidates:
            removing_pivot = removing_candidates.pop()
            # NOTICE: order matters! call recursive_removable_candidate first then remove pivot.
            candidate = recursive_removable_candidate(removing_pivot)
            self._force_remove_pivot(removing_pivot)

            while candidate and removable_pivot(candidate):
                # NOTICE: order matters! call recursive_removable_candidate first then remove pivot.
                next_candidate = recursive_removable_candidate(candidate)
                self._force_remove_pivot(candidate)

                candidate = next_candidate

    def remove_dangling_edges(self) -> None:
        # dangling edges include back turning edges
        self._remove_back_turning_edge()

        valid_edges: Set[DirectEdgeView] = set(concat(closure.edges for closure in self.closure_snapshot().closures))
        deleting_edges = lfilter(lambda edge: edge not in valid_edges, self.edges)
        self._force_remove_edges(deleting_edges, delete_reverse=False)

    def simplify_edges(self, angle_tol: float = ANGLE_AROUND_EPS,
                       cargo_union_strategy: CargoUnionStrategy = default_cargo_union_strategy) -> None:
        def removable_pivot(pivot: Pivot) -> bool:
            # pivot that satisfies conditions below should be considered a removable pivot
            # 1. has (1 in-edge and 1 out-edge) or (2 in-edges and 2-out-edges)
            # 2. this pivot only has 2 neighbor pivots
            # 3. each pair of in-edge, out-edge are parallel to each other
            # Notice: the filtering condition should not be weaker than these
            if not (len(pivot.in_edges) == len(pivot.out_edges) == 1
                    or len(pivot.in_edges) == len(pivot.out_edges) == 2):
                return False

            # pivot has exactly 2 neighbors
            if len(set(concat([(edge.from_pivot, edge.to_pivot) for edge in pivot.in_edges + pivot.out_edges]))) != 3:
                return False

            return all([edge0.shape.ext.angle().parallel_to(edge1.shape.ext.angle(), angle_tol=angle_tol)
                        for edge0, edge1 in product(pivot.in_edges, pivot.out_edges)])

        for pivot in filter(removable_pivot, self.pivots):
            in_edge: DirectEdge = pivot.in_edges[0]
            previous_pivot: Pivot = in_edge.from_pivot
            next_pivot: Pivot = in_edge.next.to_pivot
            # calculate the cargo of new DirectEdge
            union_cargo = cargo_union_strategy(in_edge.cargo, in_edge.next.cargo)

            # calculate the cargo of reverse DirectEdge of new DirectEdge above
            reverse_in_edge = in_edge.reverse
            if reverse_in_edge:
                union_cargo_of_reverse = cargo_union_strategy(reverse_in_edge.previous.cargo, reverse_in_edge.cargo)
            else:
                union_cargo_of_reverse = None

            self._force_remove_edges([*pivot.in_edges, *pivot.out_edges], delete_reverse=True, clean_dangling=False)
            self.edges.append(DirectEdge(from_pivot=previous_pivot,
                                         to_pivot=next_pivot,
                                         stretch=self,
                                         cargo=union_cargo))
            if reverse_in_edge:
                self.edges.append(DirectEdge(from_pivot=next_pivot,
                                             to_pivot=previous_pivot,
                                             stretch=self,
                                             cargo=union_cargo_of_reverse))

        self.remove_dangling_edges()
        self.remove_dangling_pivots()

    def _force_remove_edges(self, edges: Union[Sequence[DirectEdge], DirectEdge],
                            delete_reverse: bool = False,
                            clean_dangling: bool = True) -> None:
        # only used as internal method, don't use it publicly
        if not isinstance(edges, Sequence):
            edges = [edges]

        if delete_reverse:
            deleting_edge_views: Set[DirectEdge] = set(concat([(e, e.reverse) for e in edges]))
        else:
            deleting_edge_views: Set[DirectEdge] = set(edges)

        deleting_edges, self.edges = separate(lambda edge: edge in deleting_edge_views, self.edges)

        for deleting_edge in deleting_edges:
            with suppress(Exception):
                deleting_edge.from_pivot.out_edges.remove(deleting_edge)
            with suppress(Exception):
                deleting_edge.to_pivot.in_edges.remove(deleting_edge)

        if clean_dangling:
            self.remove_dangling_pivots()

    def remove_closure(self, closure_copy: ClosureView) -> None:
        self._force_remove_edges(closure_copy.edges, delete_reverse=False, clean_dangling=True)

    def union_closures(self, closure_copies: List[ClosureView]) -> None:
        if len(closure_copies) < 2:
            return

        for closure_copy0, closure_copy1 in combinations(closure_copies, 2):
            self._force_remove_edges(closure_copy0.shared_edges(closure_copy1), delete_reverse=True)

        self.remove_dangling_edges()
        self.remove_dangling_pivots()

    def _query_attachable_pivot(self, point: Point, dist_tol: float = MATH_EPS) -> Pivot:
        pivots = self.query_pivots(geom=point, buffer=dist_tol)
        return min(pivots, key=lambda pivot: pivot.shape.distance(point), default=None)

    def _query_attachable_edge(self, point: Point, dist_tol: float = MATH_EPS) -> DirectEdge:
        edges = self.query_edges(geom=point, buffer=dist_tol)
        return min(edges, key=lambda edge: edge.shape.distance(point), default=None)

    def add_pivot(self, point: Point,
                  reuse_existing: bool = True,
                  attach_to_nearest_edge: bool = True,
                  cargo: Optional[dict] = None,
                  dist_tol: float = MATH_EPS) -> Pivot:
        if not isinstance(point, Point) or not point.is_valid or point.is_empty:
            raise ValueError(f'expect valid point, given {point}')

        cargo = deepcopy(cargo) or {}
        if reuse_existing:
            if existed_pivot := self._query_attachable_pivot(point, dist_tol):
                existed_pivot.cargo = cargo
                return existed_pivot

            if attach_to_nearest_edge and (existed_edge := self._query_attachable_edge(point, dist_tol)):
                return existed_edge.expand(point, endpoint_dist_tol=dist_tol, pivot_cargo=cargo)

        new_pivot = Pivot(point, stretch=self, cargo=cargo)
        self.pivots.append(new_pivot)

        return new_pivot

    def add_closure(self, polygon: Polygon,
                    dist_tol: float = MATH_EPS,
                    edge_cargo: Optional[dict] = None,
                    pivot_cargo: Optional[dict] = None) -> List[DirectEdge]:
        if not (isinstance(polygon, Polygon) and polygon.is_valid and not polygon.is_empty):
            raise ValueError('expect a non-empty, valid polygon')

        add_reverse = unary_union(lmap(attrgetter('shape'), self.closure_snapshot().closures)).covers(polygon)
        new_edges = self._add_edge(polygon.exterior.ext.ccw(),
                                   add_reverse=add_reverse,
                                   edge_cargo=edge_cargo or {},
                                   pivot_cargo=pivot_cargo or {},
                                   dist_tol=dist_tol)
        self.remove_dangling_edges()
        return new_edges

    def split_by(self, line: Union[LineString, MultiLineString, Sequence[Union[LineString, MultiLineString]]],
                 edge_cargo: Optional[dict] = None,
                 pivot_cargo: Optional[dict] = None,
                 dist_tol: float = MATH_EPS) -> List[List[DirectEdge]]:
        from shapely.extension.util.offset import self_intersection

        line_union = unary_union(flatten(line, target_class_or_callable=LineString).to_list())

        lines_inside: List[LineString] = (self.closure_snapshot().occupation
                                          .intersection(line_union)
                                          .ext.decompose(LineString)
                                          .filter(truth)
                                          .filter_not(self_intersection)
                                          .to_list())

        new_edge_groups: List[List[DirectEdge]] = []

        for line_inside in lines_inside:
            line_inside = line_inside.simplify(0)
            new_edge_groups.append(self._add_edge(line=line_inside,
                                                  add_reverse=True,
                                                  dist_tol=dist_tol,
                                                  pivot_cargo=pivot_cargo or {},
                                                  edge_cargo=edge_cargo or {}))

        # when splitter exactly touches the closure boundary, it will create dangling edges, clean these edges here
        self.remove_dangling_edges()
        self.simplify_edges()

        cur_edge_set: Set[DirectEdge] = set(self.edges)
        existed_new_edge_groups: List[List[DirectEdge]] = []
        for edge_group in new_edge_groups:
            if edges_left := lfilter(lambda edge: edge in cur_edge_set, edge_group):
                existed_new_edge_groups.append(edges_left)

        return existed_new_edge_groups

    def _add_edge(self, line: LineString,
                  add_reverse: bool = False,
                  pivot_cargo: Optional[dict] = None,
                  edge_cargo: Optional[dict] = None,
                  dist_tol: float = MATH_EPS) -> List[DirectEdge]:
        """
        Add edge by linestring, attaching pivots and edges to each other if possible.
        NOTICE: It might introduce dangling edges!
        Parameters
        ----------
        line
        add_reverse
        pivot_cargo
        edge_cargo
        dist_tol

        Returns
        -------

        """
        add_pivot = partial(self.add_pivot,
                            reuse_existing=True,
                            attach_to_nearest_edge=True,
                            cargo=pivot_cargo or {},
                            dist_tol=dist_tol)

        # add pivots without duplicate
        points_on_line: Set[Point] = line.ext.decompose(Point).to_set()
        points_intersects_with_edges: Set[Point] = (unary_union([e.shape for e in self.edges])
                                                    .intersection(line)
                                                    .ext.decompose(Point)
                                                    .to_set())
        points: Set[Point] = points_on_line.union(points_intersects_with_edges)
        lmap(add_pivot, points)

        new_edges: List[DirectEdge] = []

        # since points of splitter have already been added to stretch, the query below will fetch out the pivots of
        # splitter points as well as the already existed pivots.
        # after sorting, each 2-pair pivot might create a new DirectEdge
        pivots_on_line_inside: List[Pivot] = self.query_pivots(line, buffer=dist_tol)
        pivots_on_line_inside.sort(key=lambda pivot: line.project(pivot.shape))

        # add edges
        origin_edge_dict: Dict[DirectEdge, DirectEdge] = {edge: edge for edge in self.edges}
        for _from_pivot, _to_pivot in win_slice(pivots_on_line_inside, win_size=2, tail_cycling=line.is_ring):
            new_edge = DirectEdge(_from_pivot, _to_pivot, stretch=self, cargo=deepcopy(edge_cargo))
            if new_edge not in origin_edge_dict:
                new_edges.append(new_edge)
            else:
                origin_edge_dict[new_edge].cargo = deepcopy(edge_cargo) or {}

            if add_reverse:
                new_reverse_edge = DirectEdge(_to_pivot, _from_pivot, stretch=self, cargo=deepcopy(edge_cargo))
                if new_reverse_edge not in origin_edge_dict:
                    new_edges.append(new_reverse_edge)
                else:
                    origin_edge_dict[new_reverse_edge].cargo = deepcopy(edge_cargo) or {}

        self.edges.extend(new_edges)
        return new_edges


class StretchFactory:
    """
    The utility for creating stretch from set of polygons
    """

    def __init__(self, dist_tol: float = MATH_EPS):
        self._dist_tol = dist_tol

    def create(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]]) -> Stretch:
        stretch = Stretch([], [])

        polys = (flatten(geom_or_geoms)
                 .filter(lambda geom: isinstance(geom, Polygon))
                 .filter(truth)
                 .to_list())

        for poly in polys:
            stretch.add_closure(poly, dist_tol=self._dist_tol)

        stretch.remove_dangling_edges()
        stretch.remove_dangling_pivots()
        return stretch


class AttachingOffset:
    """
    The utility used for calculating from-pivot or to-pivot position after offset direct edge
    """

    def __init__(self, poly: Polygon, dist_tol: float = MATH_EPS):
        self._ring = poly.exterior
        self._ring_points_aggregation = self._ring.ext.decompose(Point)
        self._dist_tol = dist_tol

    def _find_attachable_point(self, point: Point,
                               offset_vector: Vector,
                               rotating_direct_from_offset_vec: str) -> Optional[Point]:
        moved_point = offset_vector.apply(point)
        if rotating_direct_from_offset_vec == 'cw':
            ray = offset_vector.cw_perpendicular.ray(moved_point, length=self._ring.length)
        else:
            ray = offset_vector.ccw_perpendicular.ray(moved_point, length=self._ring.length)

        # add tol
        ray = ray.ext.prolong().from_head(self._dist_tol)

        points: List[Point] = []
        points.extend(ray.intersection(self._ring).ext.decompose(Point).to_list())

        query_region = ray.buffer(self._dist_tol)
        points.extend(self._ring_points_aggregation.filter(lambda pt: query_region.covers(pt)).to_list())

        return min(points, key=moved_point.distance, default=None)

    def for_from_pivot(self, edge: DirectEdge, offset_vector: Vector) -> Optional[Point]:
        offset_to_left: bool = edge.shape.ext.angle().rotating_angle(offset_vector.angle, direct='ccw').degree <= 180
        direction = ['cw', 'ccw'][offset_to_left]
        if point := self._find_attachable_point(point=edge.from_pivot.shape,
                                                offset_vector=offset_vector,
                                                rotating_direct_from_offset_vec=direction):
            return point

        other_direction = ['cw', 'ccw'][offset_to_left - 1]
        return self._find_attachable_point(point=edge.from_pivot.shape,
                                           offset_vector=offset_vector,
                                           rotating_direct_from_offset_vec=other_direction)

    def for_to_pivot(self, edge: DirectEdge, offset_vector: Vector) -> Optional[Point]:
        offset_to_left: bool = edge.shape.ext.angle().rotating_angle(offset_vector.angle, direct='ccw').degree <= 180
        direction = ['ccw', 'cw'][offset_to_left]
        if point := self._find_attachable_point(point=edge.to_pivot.shape,
                                                offset_vector=offset_vector,
                                                rotating_direct_from_offset_vec=direction):
            return point

        other_direction = ['ccw', 'cw'][offset_to_left - 1]
        return self._find_attachable_point(point=edge.to_pivot.shape,
                                           offset_vector=offset_vector,
                                           rotating_direct_from_offset_vec=other_direction)


class AttachingOffsetV2:
    def __init__(self, poly: Polygon, dist_tol: float = MATH_EPS):
        self._poly = poly
        self._dist_tol = dist_tol

    def offset_to_left(self, edge: DirectEdge, offset_vector: Vector) -> bool:
        return edge.shape.ext.angle().rotating_angle(offset_vector.angle, direct='ccw').degree <= 180

    def _cal_target_position(self, edge: DirectEdge, offset_vector: Vector, target_from_pivot: bool) -> Optional[Point]:
        offset_edge: LineString = offset_vector.apply(edge.shape)
        offset_from_point = offset_edge.ext.start()
        offset_to_point = offset_edge.ext.end()

        target_point, another_point = ((offset_from_point, offset_to_point) if target_from_pivot
                                       else (offset_to_point, offset_from_point))

        line = offset_edge
        if target_point.within(self._poly):
            if self.offset_to_left(edge, offset_vector) ^ target_from_pivot:
                ray_vec = offset_vector.cw_perpendicular
            else:
                ray_vec = offset_vector.ccw_perpendicular
            line = ray_vec.ray(target_point, self._poly.length)

        offset_edge_inside = offset_edge.intersection(self._poly)

        # candidate_projection is for covering 2 cases below
        # 1. line projects onto poly.exterior as a single point and no other points should be considered candidates
        # 2. line projects onto poly.exterior as a linestring(consisted of many points) or there are some other points
        #   on poly.exterior that are very close to the projection line, so that these points should be treated as
        #   candidate points too.
        # CAUTION: don't change the order of the elements in GeometryCollection
        # In case that candidate_points from candidate_projection all have the same distance(due to finite precision)
        # but are actually different points, pick as result the accurate one(line's intersection on poly.exterior
        # without buffer)
        candidate_projection = GeometryCollection([
            line.ext.intersection(self._poly.exterior),
            line.ext.intersection(self._poly.exterior, self_buffer=self._dist_tol)])

        # pick the closest candidate points that have distance larger than half-length of offset edge inside(candidate
        # points on another_point side)
        candidate_points: List[Point] = (
            candidate_projection
            .ext.decompose(Point)
            .filter(lambda pt: pt.distance(another_point) > offset_edge_inside.length / 2)
            .to_list())

        return min(candidate_points, key=another_point.distance)

    def for_from_pivot(self, edge: DirectEdge, offset_vector: Vector) -> Optional[Point]:
        return self._cal_target_position(edge, offset_vector, target_from_pivot=True)

    def for_to_pivot(self, edge: DirectEdge, offset_vector: Vector) -> Optional[Point]:
        return self._cal_target_position(edge, offset_vector, target_from_pivot=False)


class BaseOffsetStrategy(ABC):
    """
    Base strategy class for offset
    """

    def __init__(self, edge: DirectEdge,
                 offset_vector: Vector,
                 attaching_dist_tol: float = MATH_EPS,
                 edge_cargo_inherit_strategy: CargoInheritStrategy = default_cargo_inherit_strategy,
                 pivot_cargo_inherit_strategy: CargoInheritStrategy = default_cargo_inherit_strategy):
        self._edge = edge
        self._edge_cargo_inherit_strategy = edge_cargo_inherit_strategy
        self._pivot_cargo_inherit_strategy = pivot_cargo_inherit_strategy
        self._offset_vector = offset_vector
        self._attaching_dist_tol = attaching_dist_tol
        if not self._edge.shape.ext.angle().perpendicular_to(offset_vector.angle):
            raise ValueError(f'expect offset vector perpendicular to edge, given {edge} and {offset_vector}')

    @staticmethod
    @abstractmethod
    def does_from_pivot_use_perpendicular_mode(edge: DirectEdge, offset_vector: Vector) -> bool:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def does_to_pivot_use_perpendicular_mode(edge: DirectEdge, offset_vector: Vector) -> bool:
        raise NotImplementedError

    @property
    def stretch(self) -> Stretch:
        return self._edge.stretch

    @cached_property
    def shrinking_closure(self) -> Optional[ClosureView]:
        """
        find the closure that take self._edge as one of its edges and offset_vector make it smaller
        # TODO: draw a diagram
        Returns
        -------

        """
        edge_angle = self._edge.shape.ext.angle()
        using_edge_find_closure = edge_angle.rotating_angle(self._offset_vector.angle, direct='ccw').degree < 180
        if using_edge_find_closure:
            edge = self._edge
        elif reversed_edge := self._edge.reverse:
            edge = reversed_edge
        else:
            # reversed_edge is None, meaning
            # 1. self._edge is a single boundary edge
            # 2. self._offset_vector make the adjacent closure larger and this closure is not our target
            return None

        return ClosureView.create_from(edge.consecutive)

    def offset_from_pivot(self, edge: DirectEdge,
                          offset_vector: Vector,
                          shrinking_closure: Optional[ClosureView]) -> Pivot:
        perpendicular_mode = self.does_from_pivot_use_perpendicular_mode(edge, offset_vector)

        # perpendicular mode:
        # target point will go along line which is perpendicular to the given edge
        if perpendicular_mode:
            target_point = offset_vector.apply(edge.from_pivot.shape)
            try:
                if shrinking_closure and not shrinking_closure.shape.buffer(self._attaching_dist_tol).covers(
                        target_point):
                    # if perpendicular mode failed, try attaching mode instead
                    raise RuntimeError

                # process in perpendicular mode:
                # 1. create dangling pivot
                # 2. connect origin from_pivot to this dangling pivot
                # 3. return the dangling pivot
                dangling_pivot = self.stretch.add_pivot(target_point,
                                                        dist_tol=self._attaching_dist_tol,
                                                        cargo=self._pivot_cargo_inherit_strategy(edge.from_pivot.cargo))
                new_edge = DirectEdge(from_pivot=edge.from_pivot,
                                      to_pivot=dangling_pivot,
                                      stretch=self.stretch,
                                      cargo=self._edge_cargo_inherit_strategy(edge.cargo))
                self.stretch.edges.append(new_edge)

                if edge.reverse:
                    new_reverse_edge = DirectEdge(from_pivot=dangling_pivot,
                                                  to_pivot=edge.from_pivot,
                                                  stretch=self.stretch,
                                                  cargo=self._edge_cargo_inherit_strategy(edge.reverse.cargo))
                    self.stretch.edges.append(new_reverse_edge)

                return dangling_pivot

            except RuntimeError:
                pass  # try attaching mode instead

        # attaching mode:
        # target point will move along the boundary of given closure
        # in attaching mode, shrinking_closure must exist
        if not shrinking_closure:
            raise ValueError('probably because perpendicular mode failed')

        target_point = (AttachingOffsetV2(shrinking_closure.shape, dist_tol=self._attaching_dist_tol)
                        .for_from_pivot(edge, offset_vector))
        if not target_point:
            raise ValueError('offset_vector is too long, so that edge after offset extrudes outside the origin closure')
        return self.stretch.add_pivot(target_point,
                                      dist_tol=self._attaching_dist_tol,
                                      cargo=self._pivot_cargo_inherit_strategy(edge.from_pivot.cargo))

    def offset_to_pivot(self, edge: DirectEdge,
                        offset_vector: Vector,
                        shrinking_closure: Optional[ClosureView]) -> Pivot:
        perpendicular_mode = self.does_to_pivot_use_perpendicular_mode(edge, offset_vector)

        # perpendicular mode:
        # target point will go along line which is perpendicular to the given edge
        if perpendicular_mode:
            target_point = offset_vector.apply(edge.to_pivot.shape)
            try:
                if shrinking_closure and not shrinking_closure.shape.buffer(self._attaching_dist_tol).covers(
                        target_point):
                    # if perpendicular mode failed, try attaching mode instead
                    raise RuntimeError

                # process in perpendicular mode:
                # 1. create dangling pivot
                # 2. connect origin from_pivot to this dangling pivot
                # 3. return the dangling pivot
                dangling_pivot = self.stretch.add_pivot(target_point,
                                                        dist_tol=self._attaching_dist_tol,
                                                        cargo=self._pivot_cargo_inherit_strategy(edge.to_pivot.cargo))
                new_edge = DirectEdge(from_pivot=dangling_pivot,
                                      to_pivot=edge.to_pivot,
                                      stretch=self.stretch,
                                      cargo=self._edge_cargo_inherit_strategy(edge.cargo))
                self.stretch.edges.append(new_edge)

                if edge.reverse:
                    new_reverse_edge = DirectEdge(from_pivot=edge.to_pivot,
                                                  to_pivot=dangling_pivot,
                                                  stretch=self.stretch,
                                                  cargo=self._edge_cargo_inherit_strategy(edge.reverse.cargo))
                    self.stretch.edges.append(new_reverse_edge)
                return dangling_pivot

            except RuntimeError:
                pass  # try attaching mode instead

        # attaching mode:
        # target point will move along the boundary of given closure
        # in attaching mode, shrinking_closure must exist
        if not shrinking_closure:
            raise ValueError('probably because perpendicular mode failed')

        target_point = (AttachingOffsetV2(shrinking_closure.shape, dist_tol=self._attaching_dist_tol)
                        .for_to_pivot(edge, offset_vector))
        if not target_point:
            raise ValueError('offset_vector is too long, so that edge after offset extrudes outside the origin closure')
        return self.stretch.add_pivot(target_point,
                                      dist_tol=self._attaching_dist_tol,
                                      cargo=self._pivot_cargo_inherit_strategy(edge.to_pivot.cargo))

    @abstractmethod
    def create_new_edge(self, new_from_pivot: Pivot, new_to_pivot: Pivot) -> DirectEdge:
        raise NotImplementedError

    def do(self) -> DirectEdge:
        new_from_pivot = self.offset_from_pivot(edge=self._edge,
                                                offset_vector=self._offset_vector,
                                                shrinking_closure=self.shrinking_closure)

        new_to_pivot = self.offset_to_pivot(edge=self._edge,
                                            offset_vector=self._offset_vector,
                                            shrinking_closure=self.shrinking_closure)

        new_edge = self.create_new_edge(new_from_pivot, new_to_pivot)

        self.stretch._force_remove_edges([self._edge], delete_reverse=True)
        self.stretch.remove_dangling_edges()
        self.stretch.remove_dangling_pivots()

        return new_edge


class OffsetStrategy(BaseOffsetStrategy):
    """
    simple offset strategy that will choose attaching mode or perpendicular mode for calculating offset
    """

    def create_new_edge(self, new_from_pivot: Pivot, new_to_pivot: Pivot) -> DirectEdge:
        new_edges = [DirectEdge(from_pivot=new_from_pivot,
                                to_pivot=new_to_pivot,
                                stretch=self.stretch,
                                cargo=self._edge_cargo_inherit_strategy(self._edge.cargo))]
        if self._edge.reverse:
            new_edges.append(DirectEdge(from_pivot=new_to_pivot,
                                        to_pivot=new_from_pivot,
                                        stretch=self.stretch,
                                        cargo=self._edge_cargo_inherit_strategy(self._edge.reverse.cargo)))
        self.stretch.edges.extend(new_edges)
        return new_edges[0]

    @staticmethod
    def does_from_pivot_use_perpendicular_mode(edge: DirectEdge, offset_vector: Vector) -> bool:
        if not edge.shape.ext.angle().rotating_angle(offset_vector.angle, direct='ccw').almost_equal(90, angle_tol=1):
            # if offset vector does not point to edge's ccw perpendicular, we should use edge.reverse to
            # deduct the mode
            if not edge.reverse:
                # if no edge has no reverse, meaning that we are trying to offset a boundary edge to make closure larger
                # in this case for current strategy, we just use perpendicular mode
                return True
            return OffsetStrategy.does_to_pivot_use_perpendicular_mode(edge.reverse, offset_vector)

        previous_inversion_angle = edge.previous.shape.ext.inverse().ext.angle()
        # policy here: can be modified or inherit to a new policy
        # TODO: draw diagram here
        perpendicular_mode: bool = offset_vector.angle.including_angle(previous_inversion_angle).degree > 89

        return perpendicular_mode

    @staticmethod
    def does_to_pivot_use_perpendicular_mode(edge: DirectEdge, offset_vector: Vector) -> bool:
        if not edge.shape.ext.angle().rotating_angle(offset_vector.angle, direct='ccw').almost_equal(90, angle_tol=1):
            # if offset vector does not point to edge's ccw perpendicular,
            # we should use edge.reverse to deduct the mode
            if not edge.reverse:
                # if no edge has no reverse, meaning that we are trying to offset a boundary edge to make closure larger
                # in this case for current strategy, we just use perpendicular mode
                return True
            return OffsetStrategy.does_from_pivot_use_perpendicular_mode(edge.reverse, offset_vector)

        # policy here: can be modified or inherit to a new policy
        # TODO: draw diagram here
        perpendicular_mode: bool = offset_vector.angle.including_angle(edge.next.shape.ext.angle()).degree > 89

        return perpendicular_mode
