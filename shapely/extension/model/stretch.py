from abc import ABC, abstractmethod
from contextlib import suppress
from itertools import starmap, product
from operator import attrgetter
from typing import Union, Iterable, Dict, List, Optional, Sequence
from uuid import uuid4
from weakref import ref, ReferenceType

from functional import seq

from shapely.extension.constant import MATH_EPS, LARGE_ENOUGH_DISTANCE, MATH_MIDDLE_EPS
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.coord import Coord
from shapely.extension.model.vector import Vector
from shapely.extension.typing import Num
from shapely.extension.util.ccw import ccw
from shapely.extension.util.divide import divide
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lconcat, lfilter, lmap, group
from shapely.extension.util.iter_util import first, win_slice
from shapely.geometry import Point, Polygon, LineString, MultiLineString, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.strtree import STRtree


class StretchMixin(ABC):
    @property
    @abstractmethod
    def pivots(self) -> List["Pivot"]:
        raise NotImplementedError("pivots not implemented")

    @property
    @abstractmethod
    def shape(self) -> Union[Point, LineString, Polygon, MultiPolygon]:
        raise NotImplementedError("should implement shape property")

    def intersects(self, other: "StretchMixin"):
        if isinstance(self, Pivot) and isinstance(other, Pivot):
            return self.shape.equals(other.shape)

        return any(p1.intersects(p2) for p1, p2 in product(self.pivots, other.pivots))


class Pivot(StretchMixin):
    """
    node of stretch
    """

    def __init__(self, origin: Union[Coord, Point],
                 in_edges: Optional[List['DirectEdge']] = None,
                 out_edges: Optional[List['DirectEdge']] = None):
        try:
            self._origin = Point(origin)
        except Exception:
            raise TypeError(f'given origin cannot form a point, given {origin}')

        if not self._origin.is_valid or self._origin.is_empty:
            raise ValueError(f'origin is invalid point, given {origin}')

        self.in_edges = in_edges or []
        self.out_edges = out_edges or []
        self._stretch: Optional[ReferenceType['Stretch']] = None
        self._cargo = {}
        self._id = str(uuid4())

    def __hash__(self):
        return hash(('pivot', self._id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        return f'Pivot({self.shape.x}, {self.shape.y})@{self._id[:4]}'

    @property
    def cargo(self) -> Dict:
        return self._cargo

    @property
    def id(self) -> str:
        return self._id

    @property
    def stretch(self) -> Optional['Stretch']:
        return self._stretch if not self._stretch else self._stretch()

    @cargo.setter
    def cargo(self, cargo: Dict):
        if not isinstance(cargo, dict):
            raise TypeError(f'should specify cargo object, given {cargo}')
        self._cargo = cargo

    @stretch.setter
    def stretch(self, stretch):
        if not isinstance(stretch, Stretch):
            raise TypeError(f'should specify stretch object, given {stretch}')

        self._stretch = ref(stretch)

    @property
    def shape(self) -> Point:
        return self._origin

    @property
    def is_valid(self) -> bool:
        return len(self.in_edges) == len(self.out_edges)

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

    @property
    def pivots(self):
        return [self]


class DirectEdge(StretchMixin):
    """
    edge of stretch
    """

    def __init__(self, from_pivot: Pivot, to_pivot: Pivot):
        if from_pivot == to_pivot:
            raise ValueError('from_pivot should not be equal to to_pivot')

        self._from_pivot = from_pivot
        self._to_pivot = to_pivot
        self._closure = None
        self._cargo = {}
        self._setup()

    def _setup(self):
        if self not in self._from_pivot.out_edges:
            self._from_pivot.out_edges.append(self)
        if self not in self._to_pivot.in_edges:
            self._to_pivot.in_edges.append(self)

    def __hash__(self):
        return hash(('direct_edge', hash(self._from_pivot), hash(self._to_pivot)))

    def __eq__(self, other):
        return self._from_pivot == other.from_pivot and self._to_pivot == other.to_pivot

    def __repr__(self):
        return f'Edge(({self.from_pivot})->({self.to_pivot}))'

    @property
    def cargo(self) -> Dict:
        return self._cargo

    @property
    def from_pivot(self) -> Pivot:
        return self._from_pivot

    @property
    def to_pivot(self) -> Pivot:
        return self._to_pivot

    @cargo.setter
    def cargo(self, cargo: Dict):
        if not isinstance(cargo, dict):
            raise TypeError(f'should specify cargo object, given {cargo}')
        self._cargo = cargo

    @from_pivot.setter
    def from_pivot(self, from_pivot: Pivot):
        if not isinstance(from_pivot, Pivot):
            raise TypeError(f'should specify from_pivot object, given {from_pivot}')
        self._from_pivot = from_pivot

    @to_pivot.setter
    def to_pivot(self, to_pivot: Pivot):
        if not isinstance(to_pivot, Pivot):
            raise TypeError(f'should specify to_pivot object, given {to_pivot}')
        self._to_pivot = to_pivot

    @property
    def pivots(self) -> List[Pivot]:
        return [self.from_pivot, self.to_pivot]

    @property
    def edges(self) -> List['DirectEdge']:
        return [self]

    @property
    def closure(self) -> Optional['Closure']:
        return self._closure if not self._closure else self._closure()

    @closure.setter
    def closure(self, closure: 'Closure'):
        if not isinstance(closure, Closure):
            raise TypeError(f'should specify closure object, given {closure}')

        self._closure = ref(closure)

    @property
    def stretch(self) -> Optional['Stretch']:
        return None if not self.closure else self.closure.stretch

    @property
    def shape(self) -> StraightSegment:
        return StraightSegment([self._from_pivot.shape, self._to_pivot.shape])

    def delete(self) -> None:
        self._from_pivot.out_edges = lfilter(lambda edge: edge is not self, self._from_pivot.out_edges)
        self._to_pivot.in_edges = lfilter(lambda edge: edge is not self, self._to_pivot.in_edges)

        with suppress(Exception):
            self.closure.edges.remove(self)

    def offset(self, dist: float) -> None:
        if not isinstance(dist, Num):
            raise TypeError(f'offset only accepts number as its input, given {dist}')

        towards = 'left' if dist > 0 else 'right'
        offset_segment = self.shape.ext.offset(dist=abs(dist), towards=towards)
        from_coord = min(offset_segment.coords, key=lambda c: self._from_pivot.shape.distance(Point(c)))
        to_coord = min(offset_segment.coords, key=lambda c: self._to_pivot.shape.distance(Point(c)))
        self._from_pivot._origin = Point(from_coord)
        self._to_pivot._origin = Point(to_coord)

    def is_reverse(self, other: 'DirectEdge') -> bool:
        return self._from_pivot == other._to_pivot and self._to_pivot == other._from_pivot

    def reversed_edge(self, create_if_not_existed: bool = False) -> Optional['DirectEdge']:
        default = DirectEdge(from_pivot=self.to_pivot, to_pivot=self.from_pivot) if create_if_not_existed else None

        with suppress(Exception):
            return first(self.is_reverse, self.closure.stretch.edges, default=default)

        return default

    def intersection(self, other: 'DirectEdge') -> Optional[Union[Pivot, "DirectEdge"]]:

        intersects_pivot_in_other: List[Pivot] = lfilter(self.intersects, other.pivots)
        if len(intersects_pivot_in_other) == 2:
            return other
        if len(intersects_pivot_in_other) == 1:
            return intersects_pivot_in_other[0]
        return None

    def expand(self, point: Point, dist_tol: float = MATH_EPS) -> List['DirectEdge']:
        """
        插入一个点，生成新的有向边. 目前策略为: 存在对边时也同时expand对边
        Parameters
        ----------
        point: 待插入的点
        dist_tol:

        Returns
        -------

        """
        new_pivot = Pivot(point)
        with suppress(Exception):
            new_pivot = self.stretch.query_pivots(point)[0]

        def expand_single_edge(edge: DirectEdge) -> List[DirectEdge]:
            """
            对于单条有向边，插入一个点，生成新的有向边:
            1. 插入点位于原有向边from_p和to_p之间
            2. 若插入点与原有向边from_p或to_p重合，则返回原有向边
            Parameters
            ----------
            edge

            Returns
            -------

            """
            if (point.distance(edge.from_pivot.shape) < dist_tol
                    or point.distance(edge._to_pivot.shape) < dist_tol):
                return [edge]

            new_direct_edge_0 = DirectEdge(from_pivot=edge.from_pivot, to_pivot=new_pivot)
            new_direct_edge_1 = DirectEdge(from_pivot=new_pivot, to_pivot=edge._to_pivot)

            if edge.closure:
                try:
                    idx = edge.closure.edges.index(edge)
                    edge.closure.edges[idx:idx + 1] = [new_direct_edge_0, new_direct_edge_1]
                    new_direct_edge_0.closure = edge.closure
                    new_direct_edge_1.closure = edge.closure

                except ValueError:
                    pass

            return [new_direct_edge_0, new_direct_edge_1]

        expanded_edges = expand_single_edge(self)

        if reversed_edge := self.reversed_edge():
            expand_single_edge(reversed_edge)

        return expanded_edges

    def interpolate(self, distance: float, absolute: bool = True, dist_tol: float = MATH_EPS) -> List['DirectEdge']:
        """
        在有向边指定位置插入点，生成新的有向边
        Parameters
        ----------
        distance: 插入点距离有向边from_p的距离
        absolute: 是否使用绝对距离, 而不是相对距离
        dist_tol:

        Returns
        -------

        """
        point = self.shape.interpolate(distance, normalized=not absolute)
        return self.expand(point=point, dist_tol=dist_tol)

    def expand_by_intersection(self, line: LineString, dist_tol: float = MATH_EPS) -> List['DirectEdge']:
        point = self.shape.intersection(line.ext.prolong().from_ends(LARGE_ENOUGH_DISTANCE))
        if not (point and isinstance(point, Point)):
            return [self]
        return self.expand(point, dist_tol=dist_tol)


class MultiDirectEdge(StretchMixin):
    def __init__(self, edges: Sequence[DirectEdge]):
        self._assert_valid_edge_order(edges)
        self._edges = edges
        self._pivots = lmap(lambda edge: edge.from_pivot, self._edges) + [self._edges[-1].to_pivot]

    @staticmethod
    def _assert_valid_edge_order(edges: Sequence[DirectEdge]) -> None:
        if not edges:
            raise ValueError('given empty edges')

        for edge, next_edge in win_slice(edges, win_size=2):
            if edge.to_pivot is not next_edge.from_pivot:
                raise ValueError('edges are not in order')

    def __hash__(self):
        return hash(('multi_direct_edge', (hash(edge) for edge in self._edges)))

    def __eq__(self, other):
        if not isinstance(other, MultiDirectEdge):
            return False

        return all(edge is other_edge for edge, other_edge in zip(self._edges, other._edges))

    def __repr__(self):
        pivot_str = '->'.join(map(str, self.pivots))
        return f'Edge({pivot_str})'

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.pivots[item]
        elif isinstance(item, slice):
            return MultiDirectEdge(self.edges[item])

        raise TypeError('can only accept int or slice as index')

    @property
    def from_pivot(self) -> Pivot:
        return self._edges[0].from_pivot

    @property
    def to_pivot(self) -> Pivot:
        return self._edges[-1].to_pivot

    @property
    def pivots(self) -> List[Pivot]:
        return self._pivots

    @property
    def edges(self) -> List[DirectEdge]:
        return list(self._edges)

    @property
    def shape(self) -> LineString:
        return LineString(lmap(attrgetter('shape'), self.pivots))

    def delete(self) -> None:
        for edge in self._edges:
            edge.delete()

    def reversed_edge(self, create_if_not_existed: bool = True) -> 'MultiDirectEdge':
        return MultiDirectEdge([edge.reversed_edge(create_if_not_existed) for edge in reversed(self.edges)])


class Closure(StretchMixin):
    """
    entry of stretch
    """

    def __init__(self, edges: List[DirectEdge]):
        """

        Parameters
        ----------
        edges: 闭包所有有向边. 严格首尾相连
        """
        self._edges = self._normalize_edges(edges)
        self._stretch: Optional[ReferenceType['Stretch']] = None
        self._id = str(uuid4())
        self._cargo = {}

        for edge in self._edges:
            edge.closure = self

    @staticmethod
    def _normalize_edges(edges: Sequence[DirectEdge]) -> List[DirectEdge]:
        if not edges:
            raise ValueError('given empty edges')

        next_pivot = {edge.from_pivot: edge.to_pivot for edge in edges}
        from_pivot_to_edge = {edge.from_pivot: edge for edge in edges}

        result: List[DirectEdge] = []
        cur_edge = edges[0]

        for _ in range(len(edges)):
            result.append(cur_edge)
            cur_edge = from_pivot_to_edge.get(next_pivot.get(cur_edge.from_pivot))
            if not cur_edge:  # error case, just exit loop
                break

            if cur_edge is result[0]:  # valid case
                break

        if not result or result[-1].to_pivot is not result[0].from_pivot:
            raise ValueError('given edges cannot form valid closure')

        return result

    def __hash__(self):
        return hash(('closure', self._id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    @property
    def cargo(self) -> Dict:
        return self._cargo

    @property
    def id(self) -> str:
        return self._id

    @property
    def stretch(self) -> Optional['Stretch']:
        return self._stretch if not self._stretch else self._stretch()

    @cargo.setter
    def cargo(self, cargo: Dict):
        if not isinstance(cargo, dict):
            raise TypeError(f'should specify cargo object, given {cargo}')
        self._cargo = cargo

    @stretch.setter
    def stretch(self, stretch):
        if not isinstance(stretch, Stretch):
            raise TypeError(f'should specify stretch object, given {stretch}')

        self._stretch = ref(stretch)

    @property
    def edges(self) -> List[DirectEdge]:
        return self._edges

    @property
    def shape(self) -> Polygon:
        exterior_pts = [edge.from_pivot.shape for edge in self._edges]
        exterior_pts.append(exterior_pts[0])
        return Polygon(shell=exterior_pts)

    @property
    def pivots(self) -> List[Pivot]:
        pivots = [edge.from_pivot for edge in self.edges]
        if self.edges[-1].to_pivot is not pivots[0]:
            pivots.append(self.edges[-1].to_pivot)
        return pivots

    def delete(self) -> None:
        for edge in self.edges:
            edge.delete()

        with suppress(Exception):
            self.stretch.closures.remove(self)

    def split_to_halves(self, edge: Union[DirectEdge, MultiDirectEdge]) -> List["Closure"]:
        if not all(edge_p in set(self.pivots) for edge_p in [edge.from_pivot, edge.to_pivot]):
            raise ValueError('only accept edge with starting pivot and end pivot on current closure')

        if not self.shape.contains(edge.shape):
            return [self]

        pivot_indices = (seq(self.pivots)
                         .map(lambda pivot: pivot in edge.pivots)
                         .enumerate()
                         .filter(lambda idx_flag_pair: idx_flag_pair[1])
                         .map(lambda idx_flag_pair: idx_flag_pair[0])
                         .sorted()
                         .to_list())

        def closure_edges(existed_edges, newly_added_edge):
            if existed_edges[-1].to_pivot is not newly_added_edge.from_pivot:
                newly_added_edge = newly_added_edge.reversed_edge(create_if_not_existed=True)

            if not (existed_edges[-1].to_pivot is newly_added_edge.from_pivot
                    and existed_edges[0].from_pivot is newly_added_edge.to_pivot):
                raise ValueError('newly added edge is not suitable for existed edges to form closure,'
                                 f' given existed pivots {existed_edges[-1].to_pivot}, {existed_edges[0].from_pivot}'
                                 f' and new edge {newly_added_edge}')

            if isinstance(newly_added_edge, DirectEdge):
                return [*existed_edges, newly_added_edge]

            return [*existed_edges, *newly_added_edge.edges]

        # create first closure
        first_closure_edges = closure_edges(self.edges[pivot_indices[0]: pivot_indices[1]], edge)
        first_closure = Closure(first_closure_edges)

        # create second closure
        second_closure_edges = closure_edges(self._edges[pivot_indices[1]:] + self._edges[:pivot_indices[0]], edge)
        second_closure = Closure(second_closure_edges)

        # assign origin stretch to newborn closure
        if self.stretch:
            first_closure.stretch = self.stretch
            second_closure.stretch = self.stretch

        # since edge and pivots are shared by newborn closure,
        # so there's no need to call delete to recycle these objects.
        return [first_closure, second_closure]

    def split_by(self, edge: Union[DirectEdge, MultiDirectEdge]) -> List['Closure']:
        if isinstance(edge, DirectEdge):
            return self.split_to_halves(edge)

        # find all sub multi direct edges for splitting
        edge_pivot_indices: List[int] = (seq(edge.pivots)
                                         .map(lambda pivot: pivot in self.pivots)
                                         .enumerate()
                                         .filter(lambda idx_flag_pair: idx_flag_pair[1])
                                         .map(lambda idx_flag_pair: idx_flag_pair[0])
                                         .to_list())

        # use each sub multi direct edges to split every closure and aggregate them to get result
        closures = [self]
        for edge in [edge[i: j] for i, j in win_slice(edge_pivot_indices, win_size=2)]:
            new_closures = []
            for closure in closures:
                try:
                    new_closures.extend(closure.split_to_halves(edge))
                except ValueError:
                    new_closures.append(closure)

            closures = new_closures

        return closures

    def map_to_edge(self, line: LineString) -> Optional[MultiDirectEdge]:
        pivot_points = [pivot.shape for pivot in self.pivots]
        for pivot_point, pivot in zip(pivot_points, self.pivots):
            pivot_point.ext.cargo['pivot'] = pivot
        pivot_db = STRtree(pivot_points)

        def find_or_create_pivot(position: Point, dist: float = MATH_EPS):
            result = None

            if points := pivot_db.query(position.buffer(dist)):
                result = min(points, key=position.distance).ext.cargo.get('pivot')

            if not result:
                result = Pivot(position)

            return result

        pivots_of_line = (line.intersection(self.shape)
                          .ext.decompose(Point)
                          .map(find_or_create_pivot)
                          .to_list())
        if len(pivots_of_line) < 2:
            return None

        return MultiDirectEdge(
            [DirectEdge(pivot, next_pivot) for pivot, next_pivot in win_slice(pivots_of_line, win_size=2)
             if pivot is not next_pivot])

    # need more test
    def divided_by(self, divider: Union[LineString, MultiLineString, Sequence[LineString]]) -> List['Closure']:
        """
        用divider切分闭包，生成新的闭包
        Parameters
        ----------
        divider

        Returns
        -------

        """
        if not divider:
            return [self]

        if isinstance(divider, Sequence):
            divider = unary_union(list(divider))

        if not isinstance(divider, (LineString, MultiLineString)):
            raise TypeError(f'Type of divider is error! The divider is {divider}')

        # make each polygon ccw thus keep the closure and direct edge relationship correct
        polygons = (flatten(divide(self.shape, divider=divider), Polygon)
                    .map(lambda p: p.simplify(MATH_MIDDLE_EPS).ext.ccw())
                    .to_list())

        if len(polygons) <= 1:
            return [self]

        existed_pivots = self.stretch.pivots if self.stretch else []
        self_stretch = self.stretch
        self.delete()
        closures: List['Closure'] = []

        for cur_shape in polygons:
            ring_points = [Point(coord) for coord in cur_shape.exterior.coords[:-1]]
            ring_pivots = [first(lambda p: node.buffer(MATH_MIDDLE_EPS).covers(p.shape), existed_pivots) or Pivot(node)
                           for node in ring_points]
            existed_pivots = list(set(existed_pivots + ring_pivots))

            ring_edges: List[DirectEdge] = []
            for pivots_pair in win_slice(ring_pivots, win_size=2, tail_cycling=True):
                edge = DirectEdge(from_pivot=pivots_pair[0], to_pivot=pivots_pair[1])
                ring_edges.append(edge)

            closure = Closure(edges=ring_edges)
            closure.stretch = self_stretch
            closures.append(closure)

        self_stretch.closures.extend(closures)
        return closures

    def union(self, other: 'Closure') -> List['Closure']:
        """
        联合闭包生成新闭包(两闭包需属于同一stretch)：
            1. 两闭包不属于同一stretch时抛出异常
            2. 符合联合条件时, 得到新生成的联合闭包
            3. 不符合联合条件时, 返回原有的两个闭包

        Parameters
        ----------
        other: 待联合闭包

        Returns
        -------

        """
        if not self.stretch:
            raise ValueError('The reference of stretch is error!')

        if self.stretch != other.stretch:
            raise ValueError('The closures do not belong to same stretch!')

        if not self.intersects(other):
            return [self, other]

        edge_groups = group(lambda edge0, edge1: edge0.is_reverse(edge1), self.edges + other.edges)
        edges = (seq(edge_groups)
                 .filter(lambda grp: len(grp) == 1)
                 .flatten()
                 .to_list())

        # CAUTION: delete must precede creating new closure, otherwise it'll cause bug
        self.delete()
        other.delete()

        new_closure = Closure(edges=edges)
        self.stretch.append(new_closure)

        return [new_closure]


class Stretch:
    def __init__(self, closures: List[Closure]):
        self._closures = closures
        self._id = str(uuid4())
        self._cargo = {}
        self._setup()

    @property
    def closures(self) -> List[Closure]:
        return self._closures

    @closures.setter
    def closures(self, closures: List[Closure]):
        self._closures = closures
        self._setup()

    def _setup(self):
        for closure in self.closures:
            closure.stretch = self
            # edge's stretch is followed by its belonging closure's stretch

        for pivot in self.pivots:
            pivot.stretch = self

    def __hash__(self):
        return hash(('stretch', self._id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    @property
    def shape(self) -> MultiPolygon:
        return MultiPolygon(lmap(attrgetter('shape'), self.closures))

    @property
    def cargo(self) -> Dict:
        return self._cargo

    @cargo.setter
    def cargo(self, cargo: Dict):
        if not isinstance(cargo, dict):
            raise TypeError(f'should specify cargo object, given {cargo}')
        self._cargo = cargo

    @property
    def id(self) -> str:
        return self._id

    @property
    def edges(self) -> List[DirectEdge]:
        return lconcat([closure.edges for closure in self.closures])

    @property
    def pivots(self) -> List[Pivot]:
        return list(set(lconcat([closure.pivots for closure in self.closures])))

    @property
    def occupation(self) -> BaseGeometry:
        return unary_union([closure.shape for closure in self.closures])

    def query_pivots(self, geom: BaseGeometry) -> List[Pivot]:
        return lfilter(lambda pivot: geom.intersects(pivot.shape), self.pivots)

    def query_edges(self, geom: BaseGeometry) -> List[DirectEdge]:
        return lfilter(lambda edge: geom.intersects(edge.shape), self.edges)

    def query_closures(self, geom: BaseGeometry) -> List[Closure]:
        return lfilter(lambda closure: geom.intersects(closure.shape), self.closures)

    def delete_closures(self, closures: List[Closure]) -> None:
        for closure in closures:
            if closure in self.closures:
                closure.delete()

    def append(self, other: Closure) -> None:
        if other.stretch:
            if other.stretch == self:
                return
            else:
                self._append_closure_in_different_stretch(other)

        other.stretch = self
        self._closures.append(other)
        self._insert_breakpoint_for_closures()

    def _append_closure_in_different_stretch(self, other: Closure) -> None:
        with suppress(Exception):
            for pivot in other.pivots:
                if exist_pivot := first(lambda p: pivot.shape.equals(p.shape), self.pivots):
                    exist_pivot.in_edges.extend(pivot.in_edges)
                    exist_pivot.out_edges.extend(pivot.out_edges)
                    for edge in pivot.in_edges:
                        edge.to_pivot = exist_pivot
                    for edge in pivot.out_edges:
                        edge.from_pivot = exist_pivot
                    pivot.in_edges = []
                    pivot.out_edges = []

            other.stretch.closures.remove(other)

    def _insert_breakpoint_for_closures(self) -> None:
        endpoints = [pivot.shape for pivot in self.pivots]
        for edge in self.edges:
            for endpoint in endpoints:
                if edge.shape.contains(endpoint):
                    _ = edge.expand(endpoint)

    def divided_by(self, divider: Union[LineString, MultiLineString, Sequence[Union[LineString, MultiLineString]]]):
        lines = flatten(divider, LineString).to_list()

        for line in lines:
            for edge in self.edges:
                edge.expand_by_intersection(line)

            new_closures = []
            for closure in self.closures:
                if multi_direct_edge := closure.map_to_edge(line):
                    try:
                        new_closures.extend(closure.split_by(multi_direct_edge))
                        continue
                    except ValueError:
                        pass

                new_closures.append(closure)

            self.closures = new_closures

        return self.closures


class StretchFactory:
    def __init__(self, dist_tol: float = MATH_EPS):
        self._dist_tol = dist_tol

    def create(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]]) -> Stretch:
        if isinstance(geom_or_geoms, BaseGeometry):
            geom_or_geoms = [geom_or_geoms]

        # extract valid non-empty polygons and remove its holes
        polys = (flatten(geom_or_geoms, Polygon, validate=False)
                 .map(lambda poly: poly.ext.shell)
                 .to_list())

        if not polys:
            raise ValueError('given input should contain valid non-empty polygon with no holes')

        point_groups: List[List[Point]] = self._create_nodes_groups(polys)
        pivots: List[Pivot] = [Pivot(origin=node) for node in set(lconcat(point_groups))]

        def find_or_create_pivots(point: Point) -> Pivot:
            return first(lambda pvt: point.equals(pvt.shape), pivots, default=Pivot(point))

        closures: List[Closure] = []
        for point_group in point_groups:
            ring_pivots = lmap(find_or_create_pivots, point_group)
            ring_edges = list(starmap(DirectEdge, win_slice(ring_pivots, win_size=2, tail_cycling=True)))
            closures.append(Closure(edges=ring_edges))

        return Stretch(closures=closures)

    def _create_nodes_groups(self, polys: List[Polygon]) -> List[List[Point]]:
        """
        生成结点组. 每个geom生成一个结点列表, 该列表可有序插入其他geom生成的临近结点

        Parameters
        ----------
        polys

        Returns
        -------

        """
        point_groups = [[Point(c) for c in geom.simplify(self._dist_tol * 2).exterior.ext.ccw().coords[:-1]]
                        for geom in polys]
        for i, j in product(range(len(point_groups)), repeat=2):
            if j == i:
                continue

            for inserter in lfilter(lambda pt: polys[i].distance(pt) < self._dist_tol, point_groups[j]):
                point_groups[i] = self._insert_ring_nodes(point_groups[i], inserter, has_operated=j < i)

        return point_groups

    def _insert_ring_nodes(self, ring_nodes: List[Point], inserter: Point, has_operated: bool) -> List[Point]:
        """
        在有序的环形结点中插入结点, 其结果仍然有序

        Parameters
        ----------
        ring_nodes: 待插入结点的环状有序结点组
        inserter: 插入结点
        has_operated: 插入结点所在结点组是否已经进行过插入操作

        Returns
        -------

        """
        index = -1
        for idx_pair in win_slice(range(len(ring_nodes)), win_size=2, tail_cycling=True):
            seg = StraightSegment([ring_nodes[idx_pair[0]], ring_nodes[idx_pair[1]]])
            if seg.distance(inserter) > self._dist_tol:
                continue

            for i in range(2):
                if ring_nodes[idx_pair[i]].distance(inserter) < self._dist_tol:
                    if has_operated:
                        ring_nodes[idx_pair[i]] = inserter
                    return ring_nodes

            index = idx_pair[1]
            break

        if index > -1:
            ring_nodes.insert(index, inserter)

        return ring_nodes
