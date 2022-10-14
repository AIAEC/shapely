from typing import Union, Iterable, Dict, List, Optional
from uuid import uuid4

from shapely.extension.constant import MATH_EPS
from shapely.extension.geometry import StraightSegment
from shapely.extension.model.coord import Coord
from shapely.extension.model.vector import Vector
from shapely.extension.util.divide import divide
from shapely.extension.util.func_util import lconcat, lfilter
from shapely.extension.util.iter_util import first, win_slice
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from shapely.geometry.base import BaseGeometry


class Pivot:
    """
    node of stretch
    """

    def __init__(self, origin: Union[Coord, Point],
                 in_edges: Optional[List['DirectEdge']] = None,
                 out_edges: Optional[List['DirectEdge']] = None):
        if isinstance(origin, Coord) or isinstance(origin, tuple):
            self.origin = Point(origin)
        elif isinstance(origin, Point):
            self.origin = origin
        else:
            raise TypeError('origin is not a point or coord!')

        if not self.origin.is_valid:
            raise ValueError('origin is invalid point')

        self.in_edges = in_edges or []
        self.out_edges = out_edges or []
        self._id = str(uuid4())
        self._cargo = {}

    def __hash__(self):
        return hash(('pivot', self._id))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    @property
    def cargo(self) -> Dict:
        return self._cargo

    @property
    def shape(self) -> Point:
        return self.origin

    @property
    def is_valid(self) -> bool:
        return len(self.in_edges) == len(self.out_edges)

    # TODO: to add some different strategy
    def move_to(self, target: Union[Point, Coord]) -> None:
        if isinstance(target, Coord):
            target = Point(target)
        elif not isinstance(target, Point):
            raise TypeError('target is not a point!')
        self.origin = target

    # TODO: ditto
    def move_by(self, direct: Vector) -> None:
        self.origin = direct.apply(self.origin)


class DirectEdge:
    """
    edge of stretch
    """

    def __init__(self, from_p: Pivot, to_p: Pivot,
                 closure: Optional['Closure'] = None):
        self.from_p = from_p
        self.to_p = to_p
        self.closure = closure
        self._cargo = {}

        self.from_p.out_edges.append(self)
        self.to_p.in_edges.append(self)

    def __hash__(self):
        return hash(('direct_edge', self.from_p.__hash__(), self.to_p.__hash__()))

    def __eq__(self, other):
        return self.from_p == other.from_p and self.to_p == other.to_p

    @property
    def cargo(self) -> Dict:
        return self._cargo

    @property
    def shape(self) -> StraightSegment:
        return StraightSegment([self.from_p.origin, self.to_p.origin])

    def remove(self) -> None:
        if self in self.from_p.out_edges:
            self.from_p.out_edges.remove(self)
        if self in self.to_p.in_edges:
            self.to_p.in_edges.remove(self)

        try:
            if self in self.closure.edges:
                self.closure.edges.remove(self)
        except AttributeError:
            return

    def offset(self, dist: float) -> None:
        towards = 'left' if dist > 0 else 'right'
        offset_segment = self.shape.ext.offset(dist=abs(dist), towards=towards)
        from_c = min(offset_segment.coords, key=lambda c: self.from_p.origin.distance(Point(c)))
        to_c = min(offset_segment.coords, key=lambda c: self.to_p.origin.distance(Point(c)))
        self.from_p.origin = Point(from_c)
        self.to_p.origin = Point(to_c)

    def is_reverse(self, other: 'DirectEdge') -> bool:
        return self.from_p == other.to_p and self.to_p == other.from_p

    def reversed_edge(self) -> Optional['DirectEdge']:
        try:
            for edge in self.closure.stretch.edges:
                if self.is_reverse(edge):
                    return edge
            return None
        except AttributeError:
            return None

    # TODO: to add some different strategy
    def expand(self, extra_point: Point) -> List['DirectEdge']:
        """
        插入一个点，生成新的有向边. 目前策略为: 存在对边时也同时expand对边
        Parameters
        ----------
        extra_point: 待插入的点

        Returns
        -------

        """
        expanded_edges = self.expand_single_edge(extra_point)
        if reversed_edge := self.reversed_edge():
            expanded_edges.extend(reversed_edge.expand_single_edge(extra_point))

        return expanded_edges

    def expand_single_edge(self, extra_point: Point) -> List['DirectEdge']:
        """
        对于单条有向边，插入一个点，生成新的有向边:
        1. 插入点位于原有向边from_p和to_p之间
        2. 若插入点与原有向边from_p或to_p重合，则返回原有向边
        Parameters
        ----------
        extra_point: 待插入的点

        Returns
        -------

        """
        if extra_point.almost_equals(self.from_p.origin) or extra_point.almost_equals(self.to_p.origin):
            return [self]

        extra_pivot = Pivot(origin=extra_point)
        new_direct_edge_0 = DirectEdge(from_p=self.from_p, to_p=extra_pivot, closure=self.closure)
        new_direct_edge_1 = DirectEdge(from_p=extra_pivot, to_p=self.to_p, closure=self.closure)

        if self.closure:
            self.closure.pivots.append(extra_pivot)
            idx = self.closure.edges.index(self)
            self.closure.edges.insert(idx, new_direct_edge_0)
            self.closure.edges.insert(idx + 1, new_direct_edge_1)
        self.remove()
        return [new_direct_edge_0, new_direct_edge_1]

    def interpolate(self, distance: float, normalized: bool = False) -> List['DirectEdge']:
        """
        在有向边指定位置插入点，生成新的有向边
        Parameters
        ----------
        distance: 插入点距离有向边from_p的距离
        normalized: 是否为归一化距离. 默认为False

        Returns
        -------

        """
        extra_point = self.shape.interpolate(distance, normalized=normalized)
        return self.expand(extra_point=extra_point)


class Closure:
    """
    entry of stretch
    """

    def __init__(self, edges: List[DirectEdge], stretch: Optional['Stretch'] = None):
        """

        Parameters
        ----------
        edges: 闭包所有有向边. 严格首尾相连
        """
        self.edges = edges
        self.stretch = stretch
        self._id = str(uuid4())
        self._cargo = {}

        for edge in self.edges:
            edge.closure = self

    def __hash__(self):
        return hash(('closure', self._id))

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    @property
    def cargo(self) -> Dict:
        return self._cargo

    @property
    def shape(self) -> Polygon:
        exterior_pts = [edge.from_p.shape for edge in self.edges]
        exterior_pts.append(exterior_pts[0])
        return Polygon(shell=exterior_pts)

    @property
    def pivots(self) -> List[Pivot]:
        return list(set(lconcat([[edge.from_p, edge.to_p] for edge in self.edges])))

    def remove(self) -> None:
        for edge in self.edges:
            edge.remove()

        try:
            if self in self.stretch.closures:
                self.stretch.closures.remove(self)
        except AttributeError:
            return

    def divided_by(self, divider: Union[LineString, MultiLineString, List[LineString]]) -> List['Closure']:
        """
        用divider切分闭包，生成新的闭包
        Parameters
        ----------
        divider

        Returns
        -------

        """
        if isinstance(divider, LineString):
            return self._divided_by_single_line(divider)
        elif isinstance(divider, MultiLineString):
            divider = divider.ext.flatten(LineString)
        elif not isinstance(divider, list):
            raise TypeError('type of divider is error!')

        closures: List['Closure'] = [self]
        for single_divider in divider:
            closures = lconcat([closure._divided_by_single_line(single_divider) for closure in closures])

        return closures

    def _divided_by_single_line(self, divider: LineString) -> List['Closure']:
        if not isinstance(divider, LineString):
            raise TypeError('single divider is not a LineString')

        pre_shape = self.shape
        cur_shapes = divide(pre_shape, divider=divider)
        if len(cur_shapes) <= 1:
            return [self]

        exist_pivots = self.stretch.pivots
        closures: List['Closure'] = []
        for cur_shape in cur_shapes:
            ring_nodes = [Point(coord) for coord in cur_shape.exterior.coords[:-1]]
            ring_pivots = [first(lambda p: p.shape.almost_equals(node), exist_pivots) or Pivot(node)
                           for node in ring_nodes]
            exist_pivots = list(set(exist_pivots + ring_pivots))

            ring_edges: List[DirectEdge] = []
            for pivots_pair in win_slice(ring_pivots, win_size=2, tail_cycling=True):
                edge = DirectEdge(from_p=pivots_pair[0], to_p=pivots_pair[1])
                ring_edges.append(edge)
            closures.append(Closure(edges=ring_edges, stretch=self.stretch))

        self.stretch.closures.extend(closures)
        self.remove()
        return closures


class Stretch:
    def __init__(self, closures: List[Closure]):
        self.closures = closures

        for closure in self.closures:
            closure.stretch = self

    @property
    def edges(self) -> List[DirectEdge]:
        return lconcat([closure.edges for closure in self.closures])

    @property
    def pivots(self) -> List[Pivot]:
        return list(set(lconcat([closure.pivots for closure in self.closures])))

    def query_pivots(self, geom: BaseGeometry) -> List[Pivot]:
        return lfilter(lambda pivot: geom.intersects(pivot.shape), self.pivots)

    def query_edges(self, geom: BaseGeometry) -> List[DirectEdge]:
        return lfilter(lambda edge: geom.intersects(edge.shape), self.edges)

    def query_closures(self, geom: BaseGeometry) -> List[Closure]:
        return lfilter(lambda closure: geom.intersects(closure.shape), self.closures)

    def delete_closures(self, closures: List[Closure]) -> None:
        for closure in closures:
            if closure in self.closures:
                closure.remove()
            else:
                raise ValueError('The closure not in stretch!')


class StretchFactory:
    def __init__(self, dist_tol: float = MATH_EPS):
        self._dist_tol = dist_tol

    def create(self, geom_or_geoms: Union[BaseGeometry, Iterable[BaseGeometry]]) -> Stretch:
        if isinstance(geom_or_geoms, BaseGeometry):
            geom_or_geoms = [geom_or_geoms]
        geoms = lconcat([geom.ext.flatten().to_list() for geom in geom_or_geoms])

        # TODO:just for polygon without holes now
        if not (geoms := lfilter(lambda g: isinstance(g, Polygon) and g.is_valid and not g.interiors, geoms)):
            raise ValueError('The unit of geom_or_geoms is not valid polygon which has not holes!')

        nodes_grps = self._create_nodes_grps(geoms)
        node_set = set(lconcat(nodes_grps))
        pivots = [Pivot(origin=node) for node in list(set(node_set))]

        closures: List[Closure] = []
        for nodes_grp in nodes_grps:
            ring_pivots = [first(lambda p: p.shape.almost_equals(node), pivots) or Pivot(node) for node in nodes_grp]
            ring_edges: List[DirectEdge] = []
            for pivots_pair in win_slice(ring_pivots, win_size=2, tail_cycling=True):
                edge = DirectEdge(from_p=pivots_pair[0], to_p=pivots_pair[1])
                ring_edges.append(edge)
            closures.append(Closure(edges=ring_edges))

        return Stretch(closures=closures)

    def _create_nodes_grps(self, geoms: List[BaseGeometry]) -> List[List[Point]]:
        """
        生成结点组. 每个geom生成一个结点列表, 该列表可有序插入其他geom生成的临近结点

        Parameters
        ----------
        geoms

        Returns
        -------

        """
        nodes_grps = [[Point(c) for c in geom.boundary.ext.ccw().coords[:-1]] for geom in geoms]
        for i, nodes_grp in enumerate(nodes_grps):
            for idx in range(len(nodes_grps)):
                if idx == i:
                    continue
                if not (pre_inserters := lfilter(lambda p: geoms[i].distance(p) < self._dist_tol, nodes_grps[idx])):
                    continue

                has_operated = True if idx < i else False
                for inserter in pre_inserters:
                    nodes_grps[i] = self._insert_ring_nodes(nodes_grp, inserter, has_operated)

        return nodes_grps

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
        sign = -1
        for idx_pair in win_slice(range(len(ring_nodes)), win_size=2, tail_cycling=True):
            seg = StraightSegment([ring_nodes[idx_pair[0]], ring_nodes[idx_pair[1]]])
            if seg.distance(inserter) > self._dist_tol:
                continue

            for i in range(2):
                if ring_nodes[idx_pair[i]].distance(inserter) < self._dist_tol:
                    if has_operated:
                        ring_nodes[idx_pair[i]] = inserter
                        return ring_nodes
                    return ring_nodes

            sign = idx_pair[1]
            break

        if sign > -1:
            ring_nodes.insert(sign, inserter)

        return ring_nodes
