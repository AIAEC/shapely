from abc import ABC, abstractmethod
from contextlib import suppress
from copy import deepcopy
from dataclasses import dataclass, field
from functools import partial, cached_property
from itertools import combinations
from operator import truth, attrgetter
from typing import Union, List, Optional, Set, Sequence, Literal, Iterable
from uuid import uuid4
from weakref import ref, ReferenceType

from functional import seq
from toolz import concat

from shapely.extension.constant import MATH_EPS, ANGLE_AROUND_EPS
from shapely.extension.geometry import StraightSegment
from shapely.extension.model import Coord, Vector, Angle
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter, lmap, separate
from shapely.extension.util.iter_util import win_slice, first
from shapely.geometry import Point, Polygon, MultiPolygon, LineString, LinearRing
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


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

    def is_reversed(self, edge: 'DirectEdge') -> bool:
        return self.from_pivot == edge.to_pivot and self.to_pivot == edge.from_pivot

    @property
    def stretch(self) -> 'Stretch':
        return self._stretch()

    @property
    def shape(self) -> StraightSegment:
        return StraightSegment([self.from_pivot.shape, self.to_pivot.shape])

    @property
    def next(self) -> Optional['DirectEdge']:
        def candidate_edge(other_edge: 'DirectEdge') -> bool:
            return not (self == other_edge or self.is_reversed(other_edge))

        out_edges = lfilter(candidate_edge, self.to_pivot.out_edges)
        invert_edge_angle: Angle = self.shape.ext.inverse().ext.angle()

        def other_ccw_rotating_angle_to_inversion_of_given_edge(other_edge: DirectEdge):
            return other_edge.shape.ext.angle().rotating_angle(invert_edge_angle, direct='ccw')

        return min(out_edges, key=other_ccw_rotating_angle_to_inversion_of_given_edge, default=None)

    @property
    def previous(self) -> Optional['DirectEdge']:
        def candidate_edge(other_edge: 'DirectEdge') -> bool:
            return not (self == other_edge or self.is_reversed(other_edge))

        in_edges = lfilter(candidate_edge, self.from_pivot.in_edges)
        self_angle: Angle = self.shape.ext.angle()

        def self_ccw_rotating_angle_to_inversion_of_other_edge(other_edge: DirectEdge):
            return self_angle.rotating_angle(other_edge.shape.ext.inverse().ext.angle(), direct='ccw')

        return min(in_edges, key=self_ccw_rotating_angle_to_inversion_of_other_edge, default=None)

    def offset(self, dist: float, side: Literal['left', 'right'], edge_offset_strategy_clz: type) -> None:
        edge_vec = Vector.from_endpoints_of(self.shape)
        if side == 'left':
            offset_vec = edge_vec.ccw_perpendicular.unit(dist)
        else:
            offset_vec = edge_vec.cw_perpendicular.unit(dist)

        return edge_offset_strategy_clz(self, offset_vec).do()

    def expand(self, point: Point, endpoint_dist_tol: float = MATH_EPS) -> Pivot:
        reverse_existed = bool(self.reverse)
        closest_end_pivot = min([self.from_pivot, self.to_pivot], key=lambda pivot: pivot.distance(point))
        if closest_end_pivot.distance(point) <= endpoint_dist_tol:
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
        super().__init__(deepcopy(from_pivot), deepcopy(to_pivot), stretch)

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

    def __bool__(self):
        try:
            return self.shape.is_valid
        except:  # pivots cannot form valid polygon
            return False


@dataclass(frozen=True)
class ClosureSnapshot:
    closures: List[ClosureView] = field()

    @staticmethod
    def find_edge_ring(edge: DirectEdge) -> List[DirectEdge]:
        # TODO: explain the algorithm
        ring_edges: List[DirectEdge] = [edge]
        seen = set(ring_edges)
        while (next_edge := edge.next) and (next_edge not in seen):
            seen.add(next_edge)  # sanity guard
            ring_edges.append(next_edge)
            edge = next_edge

        return ring_edges

    @staticmethod
    def valid_ring_edges(ring_edges: List[DirectEdge]) -> bool:
        if not ring_edges:
            return False
        if ring_edges[0].from_pivot != ring_edges[-1].to_pivot:
            return False
        return all(pre.to_pivot == next_.from_pivot
                   for pre, next_ in win_slice(ring_edges, win_size=2, tail_cycling=True))

    @staticmethod
    def ring_edges_to_closure(ring_edges: List[DirectEdge]) -> Optional[ClosureView]:
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

    @classmethod
    def create_from(cls, stretch):
        edge_set: Set[DirectEdge] = set(stretch.edges)

        ring_edge_groups: List[List[DirectEdge]] = []
        guard = len(stretch.edges)
        while edge_set and guard > 0:
            guard -= 1
            starting_edge = edge_set.pop()

            edges = cls.find_edge_ring(starting_edge)
            if not cls.valid_ring_edges(edges):
                continue  # starting_edge is invalid edge, just ignore it

            ring_edge_groups.append(edges)

            edge_set.difference_update(set(edges))

        closures: List[ClosureView] = (seq(ring_edge_groups)
                                       .map(cls.ring_edges_to_closure)
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
        self.pivots: List[Pivot] = pivots
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

    def _force_remove_pivot(self, pivot: Pivot):
        # do not use this method publicly, this method is designed to be used as private method
        self._force_remove_edges([*pivot.in_edges, *pivot.out_edges], delete_reverse=True, clean_dangling=False)
        with suppress(ValueError):
            self.pivots.remove(pivot)

    def _remove_back_turning_edge(self) -> None:
        def removable_pivot(pivot: Pivot) -> bool:
            return len(pivot.in_edges) == len(pivot.out_edges) == 1 and pivot.in_edges[0].is_reversed(pivot.out_edges[0])

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

    def simplify_edges(self, angle_tol: float = ANGLE_AROUND_EPS) -> None:
        def removable_pivot(pivot: Pivot) -> bool:
            if len(pivot.in_edges) > 2 or len(pivot.out_edges) > 2:
                return False
            edges = [*pivot.in_edges, *pivot.out_edges]

            def parallel(edge0: DirectEdge, edge1: DirectEdge):
                return edge0.shape.ext.angle().parallel_to(edge1.shape.ext.angle(), angle_tol=angle_tol)

            return all([parallel(edge0, edge1) for edge0, edge1 in combinations(edges, 2)])

        for pivot in filter(removable_pivot, self.pivots):
            in_edge: DirectEdge = pivot.in_edges[0]
            previous_pivot: Pivot = in_edge.from_pivot
            next_pivot: Pivot = in_edge.next.to_pivot

            # if current in-edge-degree larger than 1, meaning edges around pivot has reverse edge
            add_reverse: bool = len(pivot.in_edges) > 1

            self._force_remove_edges([*pivot.in_edges, *pivot.out_edges], delete_reverse=True, clean_dangling=False)
            self.edges.append(DirectEdge(from_pivot=previous_pivot, to_pivot=next_pivot, stretch=self))
            if add_reverse:
                self.edges.append(DirectEdge(from_pivot=next_pivot, to_pivot=previous_pivot, stretch=self))

        self.remove_dangling_pivots()

    def _force_remove_edges(self, edges: Sequence[DirectEdge],
                            delete_reverse: bool = False,
                            clean_dangling: bool = True) -> None:
        # only used as internal method, don't use it publicly
        if delete_reverse:
            deleting_edge_views: Set[DirectEdge] = set(concat([(e, e.reverse) for e in edges]))
        else:
            deleting_edge_views: Set[DirectEdge] = set(edges)

        deleting_edges, self.edges = separate(lambda edge: edge in deleting_edge_views, self.edges)

        for deleting_edge in deleting_edges:
            deleting_edge.from_pivot.out_edges.remove(deleting_edge)
            deleting_edge.to_pivot.in_edges.remove(deleting_edge)

        if clean_dangling:
            self.remove_dangling_pivots()

    def remove_closure(self, closure_copy: ClosureView) -> None:
        self._force_remove_edges(closure_copy.edges, delete_reverse=False)

    def union_closures(self, closure_copies: List[ClosureView]) -> None:
        if len(closure_copies) < 2:
            return

        for closure_copy0, closure_copy1 in combinations(closure_copies, 2):
            self._force_remove_edges(closure_copy0.shared_edges(closure_copy1), delete_reverse=True)

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
                    dist_tol: float = MATH_EPS) -> bool:
        if not (isinstance(polygon, Polygon) and polygon.is_valid and not polygon.is_empty):
            raise ValueError('expect a non-empty, valid polygon')

        add_reverse = unary_union(lmap(attrgetter('shape'), self.closure_snapshot().closures)).covers(polygon)
        changed = self._add_edge(polygon.exterior.ext.ccw(), add_reverse=add_reverse, dist_tol=dist_tol)
        self.remove_dangling_edges()
        return changed

    def split_by(self, line: LineString,
                 dist_tol: float = MATH_EPS) -> bool:
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

        changed: bool = False

        for line_inside in lines_inside:
            line_inside = line_inside.simplify(0)
            start_point = line_inside.ext.start()
            end_point = line_inside.ext.end()

            start_inserting_edge = find_attaching_edge(start_point)
            end_inserting_edge = find_attaching_edge(end_point)
            if not (start_inserting_edge and end_inserting_edge):
                continue  # just ignore this invalid line

            changed |= self._add_edge(line=line_inside, add_reverse=True, dist_tol=dist_tol)

        # when splitter exactly touches the closure boundary, it will create dangling edges, clean these edges here
        self.remove_dangling_edges()

        return changed

    def _add_edge(self, line: LineString, add_reverse: bool = False, dist_tol: float = MATH_EPS) -> bool:
        """
        Add edge by linestring, attaching pivots and edges to each other if possible.
        NOTICE: It might introduce dangling edges!
        Parameters
        ----------
        line
        add_reverse
        dist_tol

        Returns
        -------

        """
        add_pivot = partial(self.add_pivot,
                            reuse_existing=True,
                            attach_to_nearest_edge=True,
                            dist_tol=dist_tol)

        # add pivots without duplicate
        lmap(add_pivot, line.ext.decompose(Point).to_list())

        # add edges
        new_edges: Set[DirectEdge] = set()

        # since points of splitter have already been added to stretch, the query below will fetch out the pivots of
        # splitter points as well as the already existed pivots.
        # after sorting, each 2-pair pivot might create a new DirectEdge
        pivots_on_line_inside: List[Pivot] = self.query_pivots(line, buffer=dist_tol)
        pivots_on_line_inside.sort(key=lambda pivot: line.project(pivot.shape))

        for _from_pivot, _to_pivot in win_slice(pivots_on_line_inside, win_size=2, tail_cycling=line.is_ring):
            new_edges.add(DirectEdge(_from_pivot, _to_pivot, stretch=self))
            if add_reverse:
                new_edges.add(DirectEdge(_to_pivot, _from_pivot, stretch=self))

        # remove possible duplicated edges
        new_edges.difference_update(set(self.edges))
        self.edges.extend(new_edges)

        return bool(self.edges)


class StretchFactory:
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

        return stretch


class AttachingOffset:
    def __init__(self, ring: LinearRing, dist_tol: float = MATH_EPS):
        self._ring = ring
        self._ring_points_aggregation = self._ring.ext.decompose(Point)
        self._dist_tol = dist_tol

    def _find_attachable_point(self, point: Point,
                               offset_vector: Vector,
                               direction: Literal['back', 'forward'] = 'back') -> Optional[Point]:
        moved_point = offset_vector.apply(point)
        if direction == 'back':
            ray = offset_vector.cw_perpendicular.ray(moved_point, length=self._ring.length)
        else:
            ray = offset_vector.ccw_perpendicular.ray(moved_point, length=self._ring.length)

        points = []
        points.extend(ray.intersection(self._ring).ext.decompose(Point).to_list())

        query_region = ray.buffer(self._dist_tol)
        points.extend(self._ring_points_aggregation.filter(lambda pt: query_region.covers(pt)).to_list())

        return min(points, key=moved_point.distance, default=None)

    def for_from_pivot(self, from_pivot: Pivot, offset_vector: Vector) -> Optional[Point]:
        if point := self._find_attachable_point(from_pivot.shape, offset_vector, direction='back'):
            return point
        return self._find_attachable_point(from_pivot.shape, offset_vector, direction='forward')

    def for_to_pivot(self, to_pivot: Pivot, offset_vector: Vector) -> Optional[Point]:
        if point := self._find_attachable_point(to_pivot.shape, offset_vector, direction='forward'):
            return point
        return self._find_attachable_point(to_pivot.shape, offset_vector, direction='back')


class BaseOffsetStrategy(ABC):
    def __init__(self, edge: DirectEdge, offset_vector: Vector):
        self._edge = edge
        self._offset_vector = offset_vector
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

        edge_ring: List[DirectEdge] = ClosureSnapshot.find_edge_ring(edge)
        return ClosureSnapshot.ring_edges_to_closure(edge_ring)

    def offset_from_pivot(self, edge: DirectEdge,
                          offset_vector: Vector,
                          shrinking_closure: Optional[ClosureView]) -> Pivot:
        perpendicular_mode = self.does_from_pivot_use_perpendicular_mode(edge, offset_vector)

        # perpendicular mode:
        # target point will go along line which is perpendicular to the given edge
        if perpendicular_mode:
            target_point = offset_vector.apply(edge.from_pivot.shape)
            try:
                if shrinking_closure and not shrinking_closure.shape.covers(target_point):
                    # if perpendicular mode failed, try attaching mode instead
                    raise RuntimeError

                # process in perpendicular mode:
                # 1. create dangling pivot
                # 2. connect origin from_pivot to this dangling pivot
                # 3. return the dangling pivot
                dangling_pivot = self.stretch.add_pivot(target_point)
                new_edge = DirectEdge(from_pivot=edge.from_pivot, to_pivot=dangling_pivot, stretch=self.stretch)
                self.stretch.edges.append(new_edge)

                if edge.reverse:
                    new_reverse_edge = DirectEdge(from_pivot=dangling_pivot,
                                                  to_pivot=edge.from_pivot,
                                                  stretch=self.stretch)
                    self.stretch.edges.append(new_reverse_edge)

                return dangling_pivot

            except RuntimeError:
                pass  # try attaching mode instead

        # attaching mode:
        # target point will move along the boundary of given closure
        # in attaching mode, shrinking_closure must exist
        if not shrinking_closure:
            raise ValueError('probably because perpendicular mode failed')

        target_point = (AttachingOffset(shrinking_closure.shape.exterior, dist_tol=MATH_EPS)
                        .for_to_pivot(edge.from_pivot, offset_vector))
        if not target_point:
            raise ValueError('offset_vector might be too strong')
        return self.stretch.add_pivot(target_point)

    def offset_to_pivot(self, edge: DirectEdge,
                        offset_vector: Vector,
                        shrinking_closure: Optional[ClosureView]) -> Pivot:
        perpendicular_mode = self.does_to_pivot_use_perpendicular_mode(edge, offset_vector)

        # perpendicular mode:
        # target point will go along line which is perpendicular to the given edge
        if perpendicular_mode:
            target_point = offset_vector.apply(edge.to_pivot.shape)
            try:
                if shrinking_closure and not shrinking_closure.shape.contains(target_point):
                    # if perpendicular mode failed, try attaching mode instead
                    raise RuntimeError

                # process in perpendicular mode:
                # 1. create dangling pivot
                # 2. connect origin from_pivot to this dangling pivot
                # 3. return the dangling pivot
                dangling_pivot = self.stretch.add_pivot(target_point)
                new_edge = DirectEdge(from_pivot=dangling_pivot, to_pivot=edge.to_pivot, stretch=self.stretch)
                self.stretch.edges.append(new_edge)

                if edge.reverse:
                    new_reverse_edge = DirectEdge(from_pivot=edge.to_pivot,
                                                  to_pivot=dangling_pivot,
                                                  stretch=self.stretch)
                    self.stretch.edges.append(new_reverse_edge)
                return dangling_pivot

            except RuntimeError:
                pass  # try attaching mode instead

        # attaching mode:
        # target point will move along the boundary of given closure
        # in attaching mode, shrinking_closure must exist
        if not shrinking_closure:
            raise ValueError('probably because perpendicular mode failed')

        target_point = (AttachingOffset(shrinking_closure.shape.exterior, dist_tol=MATH_EPS)
                        .for_to_pivot(edge.to_pivot, offset_vector))
        if not target_point:
            raise ValueError('offset_vector might be too strong')
        return self.stretch.add_pivot(target_point)

    def do(self) -> DirectEdge:
        new_from_pivot = self.offset_from_pivot(edge=self._edge,
                                                offset_vector=self._offset_vector,
                                                shrinking_closure=self.shrinking_closure)

        new_to_pivot = self.offset_to_pivot(edge=self._edge,
                                            offset_vector=self._offset_vector,
                                            shrinking_closure=self.shrinking_closure)

        new_edges = [DirectEdge(from_pivot=new_from_pivot, to_pivot=new_to_pivot, stretch=self.stretch)]
        if self._edge.reverse:
            new_edges.append(DirectEdge(from_pivot=new_to_pivot, to_pivot=new_from_pivot, stretch=self.stretch))

        self.stretch.edges.extend(new_edges)
        self.stretch._force_remove_edges([self._edge], delete_reverse=True)
        self.stretch.remove_dangling_edges()

        return new_edges[0]


class OffsetStrategy(BaseOffsetStrategy):
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
        perpendicular_mode: bool = (
                offset_vector.angle.rotating_angle(previous_inversion_angle, direct='ccw').degree > 89)

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
        perpendicular_mode: bool = (
                offset_vector.angle.rotating_angle(edge.next.shape.ext.angle(), direct='ccw').degree > 89)

        return perpendicular_mode
