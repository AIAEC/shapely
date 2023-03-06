from copy import deepcopy
from operator import attrgetter
from typing import List, Union, Optional, Dict

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.functional import seq
from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
from shapely.extension.model.stretch.stretch_v3 import Stretch, Pivot, Edge, EdgeSeq, Closure
from shapely.extension.util.func_util import group, separate
from shapely.extension.util.ordered_set import OrderedSet
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry


class DanglingEdgeCreator:
    """
    Edge Creator is responsible for creating dangling edge(without binding to any closure).
    """

    def __init__(self, stretch: Stretch):
        self._stretch = stretch
        self._from_pid = None
        self._to_pid = None
        self._cargo_dict = self._stretch._default_edge_cargo_dict

    def cargo(self, dict_: Dict[str, object]) -> 'DanglingEdgeCreator':
        if dict_:
            self._cargo_dict = dict_
        return self

    def from_pivot(self, from_pivot: Pivot) -> 'DanglingEdgeCreator':
        assert self._stretch.pivot(from_pivot.id) is from_pivot
        self._from_pid = from_pivot.id
        return self

    def from_pivot_by_id(self, from_pid: str) -> 'DanglingEdgeCreator':
        assert self._stretch.pivot(from_pid) is not None
        self._from_pid = from_pid
        return self

    def _query_pivot(self, query_geom: BaseGeometry) -> Pivot:
        pivots = self._stretch.pivots_by_query(query_geom)
        if not pivots:
            raise ValueError('No pivot found for query geometry')
        return min(pivots, key=lambda p: query_geom.centroid.distance(p.shape))

    def from_pivot_by_query(self, query_geom: BaseGeometry) -> 'DanglingEdgeCreator':
        self._from_pid = self._query_pivot(query_geom).id
        return self

    def to_pivot(self, to_pivot: Pivot) -> 'DanglingEdgeCreator':
        assert self._stretch.pivot(to_pivot.id) is to_pivot
        self._to_pid = to_pivot.id
        return self

    def to_pivot_by_id(self, to_pid: str) -> 'DanglingEdgeCreator':
        assert self._stretch.pivot(to_pid) is not None
        self._to_pid = to_pid
        return self

    def to_pivot_by_query(self, query_geom: BaseGeometry) -> 'DanglingEdgeCreator':
        self._to_pid = self._query_pivot(query_geom).id
        return self

    def create(self, raise_on_failure: bool = True) -> Optional[Edge]:
        assert self._from_pid is not None, 'from_pivot must be set'
        assert self._to_pid is not None, 'to_pivot must be set'

        if self._from_pid == self._to_pid:
            if raise_on_failure:
                raise ValueError('from_pivot and to_pivot must be different')
            return None

        edge = Edge(from_pid=self._from_pid,
                    to_pid=self._to_pid,
                    stretch=self._stretch,
                    cargo_dict=deepcopy(self._cargo_dict))

        if edge.id in self._stretch._edge_map:
            return self._stretch._edge_map[edge.id]

        self._stretch._edge_map[edge.id] = edge

        return edge


class ClosureCreator:
    """
    closure creator is responsible for creating closure without caring about closure redundancy.
    same edge seq can be used to create multiple different closure.
    """

    def __init__(self, stretch: Stretch, id_gen):
        self._stretch = stretch
        self._exterior: Optional[EdgeSeq] = None
        self._interiors: List[EdgeSeq] = []
        self._id_gen = id_gen
        self._cargo_dict = self._stretch._default_closure_cargo_dict

    def cargo(self, dict_: Dict[str, object]) -> 'ClosureCreator':
        if dict_:
            self._cargo_dict = dict_
        return self

    def exterior(self, edges: Union[List[Edge], EdgeSeq]) -> 'ClosureCreator':
        assert all(edge.stretch is self._stretch for edge in edges)
        if isinstance(edges, EdgeSeq):
            self._exterior = edges
        else:
            self._exterior = EdgeSeq(edges)
        return self

    def add_interior(self, edges: Union[List[Edge], EdgeSeq]) -> 'ClosureCreator':
        assert all(edge.stretch is self._stretch for edge in edges)
        if isinstance(edges, EdgeSeq):
            self._interiors.append(edges)
        else:
            self._interiors.append(EdgeSeq(edges))
        return self

    def extend_interiors(self, edge_seqs: List[EdgeSeq]) -> 'ClosureCreator':
        self._interiors.extend(edge_seqs)
        return self

    def create(self) -> Closure:
        assert isinstance(self._exterior, EdgeSeq)
        assert all(isinstance(interior, EdgeSeq) for interior in self._interiors)

        closure = Closure(exterior=self._exterior,
                          interiors=self._interiors,
                          stretch=self._stretch,
                          id_=str(next(self._id_gen)),
                          cargo_dict=deepcopy(self._cargo_dict))

        # check if same closure already exists
        for _cls in self._stretch.closures:
            if closure == _cls:
                return _cls

        self._stretch._closure_map[closure.id] = closure

        return closure


class ClosureReconstructor:
    def __init__(self, stretch: Stretch):
        self._stretch = stretch
        self._id_gen = self._stretch._cid_gen

        self._exteriors: List[EdgeSeq] = []
        self._interiors: List[EdgeSeq] = []
        self._cargo_dict = self._stretch._default_closure_cargo_dict

    def cargo(self, dict_: Dict[str, object]) -> 'ClosureReconstructor':
        if dict_:
            self._cargo_dict = dict_
        return self

    def from_edges(self, edges: List[Edge],
                   closure_strategy: Optional[ClosureStrategy] = None) -> 'ClosureReconstructor':
        assert all(edge.stretch is self._stretch for edge in edges)
        edge_set = OrderedSet(edges)

        closure_strategy = closure_strategy or ClosureStrategy()

        while edge_set:
            edge = edge_set.pop()
            edge_seq = closure_strategy.consecutive_edges(edge)

            if edge_seq.exterior_available:
                if edge.reverse in edge_seq:
                    continue
                self._exteriors.append(edge_seq)
                edge_set.difference_update(edge_seq)
            elif edge_seq.interior_available:
                self._interiors.append(edge_seq)
                edge_set.difference_update(edge_seq)

        return self

    def reconstruct(self, dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                    dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> List[Closure]:
        interiors = [interior.shape for interior in self._interiors]
        exteriors = sorted([exterior.shape for exterior in self._exteriors], key=lambda shape: shape.length)

        closures: List[Closure] = []

        for exterior in exteriors:
            # suppose that interiors must be inside polygons of exteriors
            # those interiors that are not strictly inside polygons of exteriors will be ignored
            exterior_poly = Polygon(exterior.coords)

            # one interior only can belong to one exterior, we choose the smallest exterior as the owner
            interiors_inside, interiors = separate(lambda interior: interior.within(exterior_poly), interiors)
            interior_polys: List[Polygon] = [Polygon(interior.coords) for interior in interiors_inside]

            # there might exist multiple interiors laying inside each other, in this case, we ignore those laying
            # inside other interiors
            interior_poly_groups: List[List[Polygon]] = group(lambda p0, p1: p0.within(p1), interior_polys)
            belonging_interiors = (seq(interior_poly_groups)
                                   .map(lambda _group: max(_group, key=attrgetter('area')))
                                   .map(lambda _poly: _poly.exterior)
                                   .list())

            closures.append(self._stretch.add_closure(Polygon(exterior.coords, belonging_interiors),
                                                      dist_tol_to_pivot=dist_tol_to_pivot,
                                                      dist_tol_to_edge=dist_tol_to_edge,
                                                      cargo_dict=self._cargo_dict))

        return closures
