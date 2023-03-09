import json
from collections import OrderedDict
from copy import deepcopy
from itertools import count
from operator import truth, itemgetter
from typing import List, Optional, Dict, Union, Tuple, Callable
from weakref import ref, ReferenceType

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.functional import seq
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.cargo import Cargo
from shapely.extension.model.interval import Interval
from shapely.extension.typing import CoordType
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter, argmin
from shapely.extension.util.iter_util import first, win_slice
from shapely.extension.util.ordered_set import OrderedSet
from shapely.geometry import Point, LineString, Polygon, LinearRing, MultiLineString
from shapely.geometry.base import BaseGeometry


class Pivot:
    def __init__(self, origin: CoordType,
                 stretch: 'Stretch',
                 id_: str,
                 cargo_dict: Optional[dict] = None):

        self.cargo = Cargo(data=cargo_dict, host=self)
        self._stretch: ReferenceType[Stretch] = ref(stretch)
        self.origin: Point = Point(origin)
        self._id: str = id_

        self._in_edges: List[ReferenceType[Edge]] = []
        self._out_edges: List[ReferenceType[Edge]] = []

    def __repr__(self):
        return f'Pivot({self.origin.x:.2f},{self.origin.y:.2f})@{self._id}'

    def __hash__(self):
        return hash(self._id)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __del__(self):
        self._stretch = None
        self._id = None
        self._in_edges = None
        self._out_edges = None
        self.origin = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def stretch(self) -> Optional['Stretch']:
        if self._stretch is not None:
            return self._stretch()
        return None

    @property
    def shape(self) -> Point:
        return self.origin

    @property
    def in_edges(self) -> List['Edge']:
        return [e() for e in self._in_edges]

    @property
    def out_edges(self) -> List['Edge']:
        return [e() for e in self._out_edges]

    @property
    def dangling(self) -> bool:
        return not self.in_edges and not self.out_edges

    @property
    def turning_back(self) -> bool:
        return (len(self.in_edges) == 1
                and len(self.out_edges) == 1
                and self.in_edges[0].reverse == self.out_edges[0])

    @property
    def deleted(self) -> bool:
        return self._stretch is None or self.stretch.pivot(self.id) is None

    @classmethod
    def connect(cls, pivots: List['Pivot']) -> 'EdgeSeq':
        """
        [LOW LEVEL API] connect a bunch of pivots add created edges to stretch and return the edge sequence.
        This method is basically equal to call create_edge for each pair of pivots. Closure maintenance is not considered
        Parameters
        ----------
        pivots: a sequence of pivots, in particular order

        Returns
        -------
        edge sequence
        """
        if not pivots:
            raise ValueError('pivots should not be empty')

        from shapely.extension.model.stretch.creator import DanglingEdgeCreator
        stretch = pivots[0].stretch
        edge_creator = DanglingEdgeCreator(stretch)

        edges: List[Edge] = []
        for from_pivot, to_pivot in win_slice(pivots, win_size=2):
            if from_pivot == to_pivot:
                continue
            edges.append(edge_creator.from_pivot(from_pivot).to_pivot(to_pivot).create())

        return EdgeSeq(edges)


class Edge:
    def __init__(self, from_pid: str,
                 to_pid: str,
                 stretch: 'Stretch',
                 closure: Optional['Closure'] = None,
                 cargo_dict: Optional[dict] = None):
        assert from_pid != to_pid, 'from_pid and to_pid should not be the same'
        self.cargo = Cargo(data=cargo_dict, host=self)

        self.from_pid: str = from_pid
        self.to_pid: str = to_pid
        self.from_pivot = stretch.pivot(from_pid)
        self.to_pivot = stretch.pivot(to_pid)

        assert isinstance(self.from_pivot, Pivot)
        assert isinstance(self.to_pivot, Pivot)

        self._stretch: ReferenceType[Stretch] = ref(stretch)
        self._closure = ref(closure) if closure else None

        # edge owns pivot, thus edge should be responsible for adding ref(itself) to pivot's in/out edges
        self_ref = ref(self)
        if self not in self.from_pivot.out_edges:
            self.from_pivot._out_edges.append(self_ref)

        if self not in self.to_pivot.in_edges:
            self.to_pivot._in_edges.append(self_ref)

    def __repr__(self):
        return f'Edge{self.id}'

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __len__(self):
        return 1

    def __getitem__(self, _):
        return self

    def __iter__(self):
        return iter([self])

    def __deepcopy__(self, memodict={}):  # don't remove memodict here, it's the default value of deepcopy
        # create a new edge with same from/to pivots
        edge_copy = Edge(from_pid=self.from_pid,
                         to_pid=self.to_pid,
                         stretch=self.stretch,
                         closure=self.closure,
                         cargo_dict=self.cargo.data)

        # create deepcopy of its from and to pivots
        from_pivot_copy = deepcopy(self.from_pivot, memodict)
        to_pivot_copy = deepcopy(self.to_pivot, memodict)

        # set children pivot of edge copy to the pivot deepcopies
        edge_copy.from_pivot = from_pivot_copy
        edge_copy.to_pivot = to_pivot_copy

        # set back ref of edge of its children pivot deepcopies to the edge copy
        for i in range(len(from_pivot_copy._out_edges)):
            if from_pivot_copy._out_edges[i]() is self:
                from_pivot_copy._out_edges[i] = ref(edge_copy)
                break

        for i in range(len(to_pivot_copy._in_edges)):
            if to_pivot_copy._in_edges[i]() is self:
                to_pivot_copy._in_edges[i] = ref(edge_copy)
                break

        return edge_copy

    def __del__(self):
        self.from_pid = ''
        self.from_pivot = None
        self.to_pid = ''
        self.to_pivot = None
        self._stretch = None
        self._closure = None

    @property
    def id(self) -> str:
        return f'({self.from_pid},{self.to_pid})'

    @property
    def reverse_id(self) -> str:
        return f'({self.to_pid},{self.from_pid})'

    @property
    def stretch(self) -> Optional['Stretch']:
        if self._stretch is not None:
            return self._stretch()
        return None

    @property
    def shape(self) -> StraightSegment:
        return StraightSegment([self.from_pivot.origin, self.to_pivot.origin])

    @property
    def closure(self) -> Optional['Closure']:
        return self._closure() if self._closure else None

    @closure.setter
    def closure(self, closure: 'Closure'):
        self._closure = ref(closure) if closure else None
        if isinstance(closure, Closure) and not closure.seq_of_edge(self):
            raise RuntimeError('forget to add edge to closure exterior or interiors')

    @property
    def reverse(self) -> Optional['Edge']:
        if not self.stretch:
            return None

        return self.stretch.edge(self.reverse_id)

    @property
    def reverse_closure(self) -> Optional['Closure']:
        if not self.reverse:
            return None

        return self.reverse.closure

    @property
    def is_exterior(self) -> bool:
        return self.closure and (self in self.closure.exterior)

    @property
    def is_interior(self) -> bool:
        return self.closure and (self not in self.closure.exterior)

    @property
    def deleted(self) -> bool:
        return self._stretch is None or self.stretch.edge(self.id) is None

    @property
    def pivots(self) -> Tuple[Pivot, Pivot]:
        return self.from_pivot, self.to_pivot

    def next(self, strategy: Optional['ClosureStrategy'] = None) -> Optional['Edge']:
        """
        [LOW LEVEL API] try to get next edge that SHOULD belong to the same closure
        CAUTION: the next edge may not be in the same closure, since this method only based on searching algorithm
        Returns
        -------
        Edge instance or None if not found
        """
        from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
        strategy = strategy or ClosureStrategy
        return strategy.next_edge(self)

    def prev(self, strategy: Optional['ClosureStrategy'] = None) -> Optional['Edge']:
        """
        [LOW LEVEL API] try to get prev edge that SHOULD belong to the same closure
        CAUTION: the prev edge may not be in the same closure, since this method only based on searching algorithm
        Returns
        -------
        Edge instance or None if not found
        """
        from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
        strategy = strategy or ClosureStrategy
        return strategy.prev_edge(self)

    def expand(self) -> 'Expansion':
        """
        [LOW LEVEL API] expand current edge
        Returns
        -------

        """
        from shapely.extension.model.stretch.expansion import Expansion
        return Expansion(self)

    def sub_edge(self, interval: Union[Interval, Tuple[float, float]],
                 dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                 dist_tol_to_edge: float = MATH_MIDDLE_EPS,
                 absolute: bool = True) -> 'Edge':
        """
        [LOW LEVEL API] get sub edge of current edge
        Parameters
        ----------
        interval: interval instance or tuple of 2 float

        Returns
        -------
        edge
        """
        assert interval[0] < interval[1], f'interval should be in ascending order, but got {interval}'

        points = [self.shape.interpolate(val, normalized=not absolute) for val in interval]
        pivots = [self.stretch.add_pivot(origin=point,
                                         dist_tol_to_pivot=dist_tol_to_pivot,
                                         dist_tol_to_edge=dist_tol_to_edge) for point in points]
        edge_id = f'({pivots[0].id},{pivots[1].id})'
        edge = self.stretch.edge(edge_id)
        assert edge is not None, f'edge {edge_id} should be created'
        return edge

    @classmethod
    def twist(cls, primary_edge: 'Edge',
              secondary_edge: 'Edge',
              cargo_target: Optional[Callable[['Edge', 'Edge'], 'Edge']] = None) -> 'Edge':
        """
        [LOW LEVEL API] twist primary edge and secondary edge into 1 edge
        Parameters
        -------
        primary_edge
        secondary_edge
        cargo_target: function that given primary edge and secondary edge, return the chosen one of them that the result
            cargo will follow

        Returns
        -------
        edge instance, which cargo, will inherit from primary edge's cargo
        and if their reverse edge exists, the reverse edge should inherit the cargo of reverse edge of primary edge
        """
        if primary_edge.to_pid != secondary_edge.from_pid:
            raise ValueError('current edge and given edge should be connected')

        if primary_edge.closure is not secondary_edge.closure:
            raise ValueError('current edge and given edge should belong to the same closure, or no closure')

        if primary_edge.reverse is secondary_edge:
            raise ValueError('current edge and given edge should not be reverse of each other')

        if primary_edge.reverse_closure is not secondary_edge.reverse_closure:
            raise ValueError('current edge and given edge should belong to the same reverse closure, or no closure')

        # pick the right edge for cargo inheritance
        cargo_target_edge = cargo_target(primary_edge, secondary_edge) if cargo_target else primary_edge
        cargo = cargo_target_edge.cargo.data

        reverse_cargo_target_edge = cargo_target_edge.reverse
        reverse_cargo = reverse_cargo_target_edge.cargo.data if reverse_cargo_target_edge else None

        stretch = primary_edge.stretch
        from_pid = primary_edge.from_pid
        to_pid = secondary_edge.to_pid

        origin_pivots = [primary_edge.from_pivot,
                         primary_edge.to_pivot,
                         secondary_edge.from_pivot,
                         secondary_edge.to_pivot]
        closure = primary_edge.closure
        reverse_closure = primary_edge.reverse_closure
        primary_edge_reverse = primary_edge.reverse
        secondary_edge_reverse = secondary_edge.reverse

        stretch.discard_edge(primary_edge)
        stretch.discard_edge(secondary_edge)
        twisted_edge: Edge = (stretch
                              .create_edge()
                              .cargo(cargo)
                              .from_pivot_by_id(from_pid)
                              .to_pivot_by_id(to_pid)
                              .create())

        if closure:
            assert isinstance(closure, Closure)
            seq = closure.seq_of_edge(primary_edge)
            assert seq is closure.seq_of_edge(secondary_edge)

            idx = seq._edges.index(primary_edge)
            seq._edges.remove(primary_edge)
            seq._edges.remove(secondary_edge)
            seq._edges.insert(idx, twisted_edge)

            seq.set_closure(closure)

        if reverse_closure:
            stretch.discard_edge(primary_edge_reverse)
            stretch.discard_edge(secondary_edge_reverse)
            reverse_twisted_edge = (stretch
                                    .create_edge()
                                    .cargo(reverse_cargo)
                                    .from_pivot_by_id(to_pid)
                                    .to_pivot_by_id(from_pid)
                                    .create())

            seq = reverse_closure.seq_of_edge(primary_edge_reverse)
            assert seq is reverse_closure.seq_of_edge(secondary_edge_reverse)

            idx = seq._edges.index(secondary_edge_reverse)  # symmetric
            seq._edges.remove(primary_edge_reverse)
            seq._edges.remove(secondary_edge_reverse)
            seq._edges.insert(idx, reverse_twisted_edge)

            seq.set_closure(reverse_closure)

        # remove dangling pivots
        for pivot in origin_pivots:
            if pivot.dangling:
                stretch._pivot_map.pop(pivot.id, None)

        return twisted_edge

    def offset(self, offset_handler_cls: Optional[type] = None):
        """
        [HIGH LEVEL API] offset current edge while modifying related closures
        Returns
        -------
        offset instance
        """
        from shapely.extension.model.stretch.offset import Offset
        return Offset(self, offset_handler_cls=offset_handler_cls)


class EdgeSeq:
    def __init__(self, edges: List[Edge]):
        self.assert_valid_seq_of_edges(edges)

        if edges and edges[0].from_pid == edges[-1].to_pid:
            # if given edges can form a ring, rotate the list of edges to put the one with minimal id as the first one
            # thus for given ring edges list, the edge sequence will be unique and stable,
            # make default __eq__ work well.
            head_idx = argmin(edges, key=lambda e: e.id)
            edges = edges[head_idx:] + edges[:head_idx]

        self._edges: List[Edge] = edges

    @classmethod
    def from_consecutive_of(cls, edge: Edge, strategy: Optional['ClosureStrategy'] = None) -> 'EdgeSeq':
        from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
        strategy = strategy or ClosureStrategy
        return strategy.consecutive_edges(edge)

    def __repr__(self):
        pivot_ids = ','.join(self.pids)
        return f'EdgeSeq({pivot_ids})'

    def __iter__(self):
        return iter(self._edges)

    def __contains__(self, item):
        if isinstance(item, Edge):
            return item in self._edges
        elif isinstance(item, EdgeSeq):
            return all(e in self._edges for e in item)
        return False

    def __len__(self):
        return len(self._edges)

    def __getitem__(self, item):
        edge = self._edges.__getitem__(item)
        if isinstance(item, slice):
            return EdgeSeq(edge)
        return edge

    def __eq__(self, other):
        return self._edges == getattr(other, '_edges', None)

    def __hash__(self):
        return hash(tuple(self._edges))

    @property
    def from_pid(self) -> str:
        return self._edges[0].from_pid

    @property
    def from_pivot(self) -> Pivot:
        return self.stretch.pivot(self.from_pid)

    @property
    def to_pid(self) -> str:
        return self._edges[-1].to_pid

    @property
    def to_pivot(self) -> Pivot:
        return self.stretch.pivot(self.to_pid)

    @property
    def stretch(self) -> Optional['Stretch']:
        return self._edges[0].stretch if self._edges else None

    @property
    def reverse(self) -> Optional['EdgeSeq']:
        if not self._edges or not self.stretch:
            return None
        if any(edge.reverse is None for edge in self._edges):
            return None
        return EdgeSeq([e.reverse for e in reversed(self._edges)])

    @property
    def closures(self) -> List['Closure']:
        return [e.closure for e in self._edges if e.closure]

    def set_closure(self, closure: 'Closure'):
        for e in self._edges:
            e.closure = closure
        if self not in [closure.exterior] + closure.interiors:
            raise RuntimeError('forget to add edge seq to closure')

    @property
    def closure(self) -> Optional['Closure']:
        """
        mimic of closure property of Edge
        Returns
        -------
        if there are closures, pick the 1st, otherwise return None
        """
        closures = self.closures
        if not closures:
            return None
        return closures[0]

    @closure.setter
    def closure(self, closure: 'Closure'):
        self.set_closure(closure)

    @property
    def closed(self) -> bool:
        if len(self._edges) > 1:
            return self._edges[0].from_pid == self._edges[-1].to_pid
        return False

    @property
    def dangling(self) -> bool:
        """
        return if the edge seq is dangling, which is a closed edge seq that only contains back and forth edges

                   o2
                   ▲─┐
                   │ │
                   │ │
                   │ │
         o┌───────►o◄┘
         0◄───────┘1
        Returns
        -------
        bool
        """
        if not self.closed:
            return False

        stack = []
        for pid in self.pids:
            if stack and stack[-1] == pid:
                stack.pop()
            elif len(stack) > 1 and stack[-2] == pid:
                stack.pop()
                stack.pop()
            else:
                stack.append(pid)

        return not bool(stack)

    @property
    def exterior_available(self) -> bool:
        if self.closed:
            if self.dangling:  # dangling edge seq ring cannot be exterior
                return False

            assert isinstance(self.shape, LinearRing)
            is_ccw = self.shape.is_ccw

            try:
                occupation = Polygon(self.shape).area > 0
            except Exception:
                occupation = False

            return is_ccw and occupation

        return False

    @property
    def interior_available(self) -> bool:
        if self.closed:
            if self.dangling:  # dangling edge seq ring can only be interior
                return True

            assert isinstance(self.shape, LinearRing)
            is_cw = not self.shape.is_ccw

            try:
                occupation = Polygon(self.shape).area > 0
            except Exception:
                occupation = False

            return is_cw or not occupation
        return False

    @property
    def pivots(self) -> List[Pivot]:
        if not self._edges:
            return []
        return [e.from_pivot for e in self._edges] + [self._edges[-1].to_pivot]

    @property
    def pids(self) -> List[str]:
        return [p.id for p in self.pivots]

    @property
    def shape(self) -> Union[LineString, LinearRing]:
        points = [p.shape for p in self.pivots]
        if self.closed:
            return LinearRing(points)
        return LineString(points)

    @property
    def deleted(self) -> bool:
        return any(e.deleted for e in self._edges)

    def offset(self, offset_handler_cls: Optional[type] = None):
        """
        Returns
        -------
        offset instance
        """
        from shapely.extension.model.stretch.offset import Offset
        return Offset(self, offset_handler_cls=offset_handler_cls)

    def replace_and_discard(self, old_edge: Union[Edge, 'EdgeSeq'],
                            new_edge: Union[Edge, List[Edge], 'EdgeSeq']) -> None:
        """
        [LOW LEVEL API] replace old edge with new edge or edges, then discard old edge. the back ref of old edge's
        pivot will be set to the given new edges

        if given new_edge_or_edges break the chain of edges, raise ValueError

        Parameters
        ----------
        old_edge: edge or edge_seq instance
        new_edge: edge instance, list of edge instances, or edge sequence instance

        Returns
        -------
        None
        """
        if len(new_edge) < 1:
            raise ValueError('given new_edges should not be empty')

        # check if new_edges are chained
        self.assert_valid_seq_of_edges(list(new_edge))

        # check if new_edges are valid to replace old_edge
        if old_edge.from_pid != new_edge[0].from_pid or old_edge.to_pid != new_edge[-1].to_pid:
            raise ValueError('given new_edges are not valid to replace old_edge')

        if old_edge not in self:
            raise ValueError(f'old_edge {old_edge} are not all in self._edges')

        # if old edge is not in self._edges, raise ValueError
        old_edge_idx = self._edges.index(old_edge[0])
        old_edge_from_pivot = old_edge.from_pivot
        old_edge_to_pivot = old_edge.to_pivot

        # passing all checks, it's safe to do the replacement
        self._edges[old_edge_idx: old_edge_idx + len(old_edge)] = new_edge

        if self.stretch:
            _old_edges = old_edge
            if isinstance(old_edge, Edge):
                _old_edges = [old_edge]

            for _old_edge in _old_edges:
                self.stretch.discard_edge(_old_edge)

        ref_to_first_new_edge = ref(new_edge[0])
        if ref_to_first_new_edge not in old_edge_from_pivot._out_edges:
            old_edge_from_pivot._out_edges.append(ref_to_first_new_edge)

        ref_to_last_new_edge = ref(new_edge[-1])
        if ref_to_last_new_edge not in old_edge_to_pivot._in_edges:
            old_edge_to_pivot._in_edges.append(ref_to_last_new_edge)

    def simplify(self, angle_tol: float = MATH_MIDDLE_EPS,
                 consider_cargo_equality: bool = True,
                 cargo_target: Optional[Callable[[Edge, Edge], Edge]] = None) -> None:
        """
        [MID LEVEL API] simplify the edge sequence by merging edges that are almost parallel
        Parameters
        ----------
        angle_tol: float, angle degree tolerance
        consider_cargo_equality:
        cargo_target: callable, given 2 edges, return the one whose cargo simplified edge should take, if None,
            always that the cargo of primary edge.

        Returns
        -------
        None
        """

        def should_be_simplified(edge0, edge1) -> bool:
            if edge0.closure is not edge1.closure:
                return False

            if edge0.to_pid != edge1.from_pid:
                return False

            if edge0.reverse_closure != edge1.reverse_closure:
                return False

            if consider_cargo_equality and not edge0.cargo.data_equals(edge1.cargo):
                return False

            return edge0.shape.ext.angle().almost_equal(edge1.shape.ext.angle(), angle_tol)

        closed = self.closed
        merged_edges = [self._edges[0]]
        for edge in self._edges[1:]:
            if should_be_simplified(merged_edges[-1], edge):
                merged_edges[-1] = Edge.twist(merged_edges[-1], edge, cargo_target)
            else:
                merged_edges.append(edge)

        if closed and should_be_simplified(merged_edges[-1], merged_edges[0]):
            merged_edges[0] = Edge.twist(merged_edges.pop(), merged_edges[0], cargo_target)

        self._edges = merged_edges

    def remove_crack(self, from_pivots: Optional[List[Pivot]] = None,
                     gc: bool = False) -> None:
        """

        Parameters
        ----------
        from_pivots: list of pivots to start removing crack from, if not given, take all pivots as start
        gc: whether discard dangling pivots after removing crack

        Returns
        -------

        """
        pivots = set(self.pivots)
        if from_pivots:
            pivots &= set(from_pivots)

        pivots_turning_back = [p for p in pivots if p.turning_back]

        while pivots_turning_back:
            pivot = pivots_turning_back.pop()

            if pivot.deleted:
                continue

            if pivot.dangling:
                # remove those becoming dangling after removing other edges
                if gc:
                    self.stretch._pivot_map.pop(pivot.id, None)
                continue

            next_pivot = pivot.out_edges[0].to_pivot

            for edge in pivot.in_edges + pivot.out_edges:
                self.stretch.discard_edge(edge)

            if gc and pivot.dangling:
                self.stretch._pivot_map.pop(pivot.id, None)

            if next_pivot.turning_back:
                pivots_turning_back.append(next_pivot)

        self._edges = [e for e in self._edges if not e.deleted]

    @staticmethod
    def assert_valid_seq_of_edges(edges: List[Edge]) -> None:
        """
        assert valid seq of edges, with each pair of edges, the front one's to_pid is the back one's from_pid
        Parameters
        ----------
        edges: list of edges

        Returns
        -------
        None
        """
        if len(edges) <= 1:
            return
        for i in range(len(edges) - 1):
            if edges[i].to_pid != edges[i + 1].from_pid:
                raise ValueError(f'edges {edges[i].id} and {edges[i + 1].id} are not consecutive')


class Closure:
    def __init__(self, exterior: EdgeSeq,
                 stretch: 'Stretch',
                 id_: str,
                 interiors: Optional[List[EdgeSeq]] = None,
                 cargo_dict: Optional[dict] = None):
        self.cargo = Cargo(data=cargo_dict, host=self)
        self.exterior: EdgeSeq = exterior
        self.interiors: List[EdgeSeq] = interiors or []
        self._stretch: ReferenceType[Stretch] = ref(stretch)
        self._id = id_

        # closure owns edgeSeq and edges, thus closure should be responsible for set ref(itself) to edges' closure
        for edge_seq in [self.exterior] + self.interiors:
            edge_seq.set_closure(self)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Closure):
            return False

        return self.exterior == other.exterior and self.interiors == other.interiors

    def __repr__(self):
        exterior_pids = self.exterior.pids
        interior_pids_list = [i.pids for i in self.interiors]

        id_segs = []
        for ring_ids in [exterior_pids] + interior_pids_list:
            id_seg = ','.join(ring_ids)
            id_segs.append(f'[{id_seg}]')
        union_id = ','.join(id_segs)
        return f'Closure({union_id})@{self._id}'

    def __deepcopy__(self, memodict={}):
        closure = Closure(exterior=deepcopy(self.exterior, memodict),
                          stretch=self.stretch,
                          id_=self.id,
                          interiors=deepcopy(self.interiors, memodict),
                          cargo_dict=self.cargo.data)
        closure.exterior.closure = closure
        for interior in closure.interiors:
            interior.closure = closure

        return closure

    def __del__(self):
        self._stretch = None
        self._id = None
        self.exterior = None
        self.interiors = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def edges(self) -> List[Edge]:
        edges = list(self.exterior)
        for interior in self.interiors:
            edges.extend(interior)
        return edges

    @property
    def stretch(self) -> Optional['Stretch']:
        if self._stretch is not None:
            return self._stretch()
        return None

    @property
    def shape(self):
        return Polygon(self.exterior.shape, lfilter(truth, [i.shape for i in self.interiors]))

    @property
    def deleted(self) -> bool:
        return self._stretch is None or self.stretch.closure(self.id) is None

    def seq_of_edge(self, edge: Edge) -> Optional[EdgeSeq]:
        """
        return the edge sequence that contains the given edge
        Parameters
        ----------
        edge: edge instance

        Returns
        -------
        edge sequence instance if found, otherwise None
        """
        for seq in [self.exterior] + self.interiors:
            if edge in seq:
                return seq
        return None

    def cut(self, line: Union[LineString, MultiLineString],
            dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
            dist_tol_to_edge: float = MATH_MIDDLE_EPS,
            closure_strategy: Optional['ClosureStrategy'] = None) -> List['Closure']:
        """
        cut the closure by the given line, if failed return list with only current closure itself
        Notice that this method might delete the origin closure and create new closures
        Parameters
        ----------
        line: non empty linestring
        dist_tol_to_pivot: max attaching distance to existed pivots
        dist_tol_to_edge: max attaching distance to existed edges
        closure_strategy: closure strategy class

        Returns
        -------
        list of closures
        """

        from shapely.extension.model.stretch.cut import Cut
        return (Cut([self], closure_strategy)
                .by(line=line, dist_tol_to_pivot=dist_tol_to_pivot, dist_tol_to_edge=dist_tol_to_edge)
                .closures())

    def split(self, line: Union[LineString, MultiLineString],
              dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
              dist_tol_to_edge: float = MATH_MIDDLE_EPS,
              closure_strategy: Optional['ClosureStrategy'] = None) -> List['Closure']:
        """
        cut the closure by the given line, but when it will not generate back and forth edges and turning back pivots
        Parameters
        ----------
        line: non empty linestring
        dist_tol_to_pivot: max attaching distance to existed pivots
        dist_tol_to_edge: max attaching distance to existed edges
        closure_strategy: closure strategy class

        Returns
        -------
        list of closure
        """
        # get stretch before cut to avoid self closure removed by cut
        stretch = self.stretch

        closures = self.cut(line=line,
                            dist_tol_to_pivot=dist_tol_to_pivot,
                            dist_tol_to_edge=dist_tol_to_edge,
                            closure_strategy=closure_strategy)

        pivots_on_line: List[Pivot] = stretch.pivots_by_query(line, buffer_dist=dist_tol_to_pivot)

        for closure in closures:
            closure.remove_crack(from_pivots=pivots_on_line, gc=True)

        return closures

    def shared_edges(self, closure: 'Closure', including_reverse: bool = False) -> List[Edge]:
        """
        return the edges of current closure whose reverse edge is in the given closure
        Parameters
        ----------
        closure: other closure instance
        including_reverse: whether to include the reverse edge of the shared edge

        Returns
        -------
        list of edges
        """
        edges = lfilter(lambda edge: edge.reverse_closure is closure, self.edges)
        if including_reverse:
            edges.extend([edge.reverse for edge in edges])
        return edges

    def union(self, closure: 'Closure') -> List['Closure']:
        """
        union current closure with the given one, if failed return list with current closure and the given one
        Parameters
        ----------
        closure: other closure instance

        Returns
        -------
        list of closures
        the cargos of them should inherit from self.cargo
        """
        edges_shared = self.shared_edges(closure, including_reverse=True)
        if not edges_shared:
            return [self, closure]

        edges_left = OrderedSet(self.edges + closure.edges)
        edges_left.difference_update(edges_shared)

        # keep the stretch as local var, in case that delete edge might delete related closure, causing current closure
        # to be deleted and self.stretch unset to None
        stretch = self.stretch

        for edge_shared in edges_shared:
            if edge_shared.reverse:
                stretch.delete_edge(edge_shared.reverse, with_min_cost=False, gc=False)
            stretch.delete_edge(edge_shared, with_min_cost=False, gc=False)

        stretch.delete_closure(self)

        # might create dangling pivots, remove these pivots
        stretch.remove_dangling_pivots()

        from shapely.extension.model.stretch.creator import ClosureReconstructor
        closures = (ClosureReconstructor(stretch)
                    .cargo(self.cargo.data)
                    .from_edges(list(edges_left))
                    .reconstruct())

        return closures

    def difference(self, polygon,
                   dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                   dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> List['Closure']:
        if polygon.disjoint(self.shape):
            return [self]

        new_shape = self.shape.difference(polygon)

        stretch = self.stretch
        stretch.delete_closure(self, gc=True)

        new_closures: List[Closure] = []
        for poly in new_shape.ext.flatten(Polygon):
            new_closures.append(stretch.add_closure(polygon=poly,
                                                    dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge))

        # might create dangling pivots, remove these pivots
        stretch.remove_dangling_pivots()

        return new_closures

    def simplify(self, angle_tol: float = MATH_MIDDLE_EPS,
                 consider_cargo_equality: bool = True,
                 cargo_target: Optional[Callable[[Edge, Edge], Edge]] = None) -> None:
        """
        [MID LEVEL API] simplify the exterior and interiors of the closure
        Parameters
        ----------
        angle_tol: angle degree tolerance
        consider_cargo_equality:
        cargo_target

        Returns
        -------
        None
        """
        self.exterior.simplify(angle_tol, consider_cargo_equality, cargo_target)
        for interior in self.interiors:
            interior.simplify(angle_tol, consider_cargo_equality, cargo_target)

    def remove_crack(self, from_pivots: Optional[List[Pivot]] = None, gc: bool = False) -> None:
        self.exterior.remove_crack(from_pivots=from_pivots, gc=gc)

        for interior in self.interiors:
            interior.remove_crack(from_pivots=from_pivots, gc=gc)

        self.interiors = lfilter(truth, self.interiors)


class Stretch:
    def __init__(self, default_pivot_cargo_dict: Optional[dict] = None,
                 default_edge_cargo_dict: Optional[dict] = None,
                 default_closure_cargo_dict: Optional[dict] = None):

        self._pivot_map: Dict[str, Pivot] = OrderedDict()
        self._edge_map: Dict[str, Edge] = OrderedDict()
        self._closure_map: Dict[str, Closure] = OrderedDict()

        self._pid_gen = count(0)  # pivot id generator
        self._cid_gen = count(0)  # closure id generator

        self._default_pivot_cargo_dict = default_pivot_cargo_dict or {}
        self._default_edge_cargo_dict = default_edge_cargo_dict or {}
        self._default_closure_cargo_dict = default_closure_cargo_dict or {}

    def __deepcopy__(self, memodict={}):
        stretch = Stretch()
        stretch._pivot_map = deepcopy(self._pivot_map, memodict)
        stretch._edge_map = deepcopy(self._edge_map, memodict)
        stretch._closure_map = deepcopy(self._closure_map, memodict)

        stretch._default_pivot_cargo_dict = deepcopy(self._default_pivot_cargo_dict, memodict)
        stretch._default_edge_cargo_dict = deepcopy(self._default_edge_cargo_dict, memodict)
        stretch._default_closure_cargo_dict = deepcopy(self._default_closure_cargo_dict, memodict)

        stretch.shrink_id_gen()

        for pivot in stretch.pivots:
            pivot._stretch = ref(stretch)
            for i, in_edge in enumerate(pivot.in_edges):
                pivot._in_edges[i] = ref(stretch.edge(in_edge.id))
            for i, out_edge in enumerate(pivot.out_edges):
                pivot._out_edges[i] = ref(stretch.edge(out_edge.id))

        for edge in stretch.edges:
            edge._stretch = ref(stretch)
            if edge.closure:
                edge.closure = stretch.closure(edge.closure.id)

        for closure in stretch.closures:
            closure._stretch = ref(stretch)

        return stretch

    def dumps(self) -> str:
        """
        dump stretch to json string, for only debug purpose
        Returns
        -------
        json string
        """
        pivot_map = {pivot.id: pivot.shape.coords[0] for pivot in self.pivots}
        pivot_cargo_map = {pivot.id: pivot.cargo.data for pivot in self.pivots}

        edge_cargo_map = {edge.id: edge.cargo.data for edge in self.edges}

        closure_map = {closure.id: {
            'exterior': closure.exterior.pids,
            'interiors': [interior.pids for interior in closure.interiors]
        } for closure in self.closures}
        closure_cargo_map = {closure.id: closure.cargo.data for closure in self.closures}

        stretch_json = {
            "pivot": pivot_map,
            "pivot_cargo": pivot_cargo_map,
            "edge_cargo": edge_cargo_map,
            "closure": closure_map,
            "closure_cargo": closure_cargo_map,
        }
        return json.dumps(stretch_json)

    @classmethod
    def loads(cls, json_str: str) -> 'Stretch':
        """
        load stretch from json string, for only debug purpose
        Parameters
        ----------
        json_str: string of json

        Returns
        -------
        instance of stretch
        """
        stretch_json = json.loads(json_str)
        assert "pivot" in stretch_json and "closure" in stretch_json, "invalid stretch json"

        pivot_map = stretch_json["pivot"]
        closure_map = stretch_json["closure"]
        pivot_cargo_map = stretch_json["pivot_cargo"]
        closure_cargo_map = stretch_json["closure_cargo"]
        edge_cargo_map = stretch_json["edge_cargo"]

        stretch = Stretch()
        pivots: List[Pivot] = [Pivot(point, stretch, pid, pivot_cargo_map.get(pid, {}))
                               for pid, point in pivot_map.items()]

        stretch._pivot_map = OrderedDict([(pivot.id, pivot) for pivot in pivots])

        edges: List[Edge] = []
        closures: List[Closure] = []
        for cid, closure_json in closure_map.items():
            exterior = closure_json["exterior"]
            interiors = closure_json["interiors"]
            edge_seqs: List[EdgeSeq] = []

            for pid_list in [exterior] + interiors:
                cur_edges: List[Edge] = []
                for edge in [Edge(pid0, pid1, stretch) for pid0, pid1 in win_slice(pid_list, win_size=2)]:
                    edge.cargo.update(edge_cargo_map.get(edge.id, {}))
                    cur_edges.append(edge)

                edges.extend(cur_edges)
                edge_seqs.append(EdgeSeq(cur_edges))

            closures.append(Closure(exterior=edge_seqs[0],
                                    interiors=edge_seqs[1:],
                                    stretch=stretch,
                                    id_=cid,
                                    cargo_dict=closure_cargo_map.get(cid, {})))

        stretch._edge_map = OrderedDict([(edge.id, edge) for edge in edges])
        stretch._closure_map = OrderedDict([(closure.id, closure) for closure in closures])
        stretch.shrink_id_gen()
        return stretch

    def shrink_id_gen(self):
        self._pid_gen = count(max([int(i) + 1 for i in self._pivot_map.keys()], default=0))
        self._cid_gen = count(max([int(i) + 1 for i in self._closure_map.keys()], default=0))

    def edge(self, eid: str) -> Optional[Edge]:
        """
        query edge by edge id
        Parameters
        ----------
        eid: edge id

        Returns
        -------
        if found, return edge, else return None
        """
        return self._edge_map.get(eid, None)

    @property
    def edges(self) -> List[Edge]:
        """
        Returns
        -------
        all edges in stretch
        """
        return list(self._edge_map.values())

    def edge_seq(self, pids: List[str]) -> EdgeSeq:
        """
        query edge sequence by pivot ids
        Parameters
        ----------
        pids: pivot ids

        Returns
        -------
        if found, return edge sequence, else return None
        """
        return EdgeSeq([self.edge(f"({pid0},{pid1})") for pid0, pid1 in win_slice(pids, win_size=2)])

    def edges_by_query(self, query_geom: BaseGeometry, buffer_dist: float = 0.0) -> List[Edge]:
        """
        query edges by geometry
        Parameters
        ----------
        query_geom: geometry instance
        buffer_dist: buffer distance

        Returns
        -------
        list of edges
        """
        if buffer_dist != 0:
            query_geom = query_geom.buffer(buffer_dist)

        return [edge for edge in self.edges if edge.shape.intersects(query_geom)]

    def find_edge(self, query_geom: BaseGeometry, buffer_dist: float = 0.0) -> Optional[Edge]:
        """
        find best matched edge, if not found, return None
        Parameters
        ----------
        query_geom: geometry instance
        buffer_dist: buffer distance

        Returns
        -------
        edge or None
        """
        edges = self.edges_by_query(query_geom, buffer_dist)

        if len(edges) == 0:
            return None

        if len(edges) == 1:
            return edges[0]

        def projection_direction_tuple(edge: Edge) -> float:
            projection_len = (seq(edge.shape.ext.projection_by(query_geom).positive_intervals())
                              .map(lambda interval: interval.length)
                              .sum())
            including_angle = edge.shape.ext.angle().including_angle(query_geom.ext.angle()).degree
            # projection length as the primary sorting key, the larger, the better
            # including angle as the secondary sorting key, the smaller, the better
            return (projection_len, -including_angle)

        return max(edges, key=projection_direction_tuple)

    def pivot(self, pid: str) -> Optional[Pivot]:
        """
        query pivot by pivot id
        Parameters
        ----------
        pid: pivot id

        Returns
        -------
        if found, return pivot, else return None
        """
        return self._pivot_map.get(pid, None)

    @property
    def pivots(self) -> List[Pivot]:
        """
        Returns
        -------
        all pivots in stretch
        """
        return list(self._pivot_map.values())

    def pivots_by_query(self, query_geom: BaseGeometry, buffer_dist: float = 0.0) -> List[Pivot]:
        """
        query pivots by intersecting geometry
        Parameters
        ----------
        query_geom
        buffer_dist

        Returns
        -------
        pivots intersecting query_geom
        """
        if buffer_dist != 0:
            query_geom = query_geom.buffer(buffer_dist)
        return lfilter(lambda p: p.shape.intersects(query_geom), self.pivots)

    def find_pivot(self, query_geom: BaseGeometry, buffer_dist: float = 0.0) -> Optional[Pivot]:
        """
        find best matched pivot, if not found, return None
        Parameters
        ----------
        query_geom: geometry instance
        buffer_dist: buffer distance

        Returns
        -------
        pivot or None
        """
        pivots = self.pivots_by_query(query_geom, buffer_dist)

        if len(pivots) == 0:
            return None

        return min(pivots, key=lambda pivot: pivot.shape.centroid.distance(query_geom.centroid))

    def closure(self, cid: str) -> Optional[Closure]:
        """
        query closure by closure id
        Parameters
        ----------
        cid: closure id

        Returns
        -------
        if found, return closure, else return None
        """
        return self._closure_map.get(cid, None)

    def closures_by_query(self, query_geom: BaseGeometry, buffer_dist: float = 0.0) -> List[Closure]:
        """
        query closure by intersecting geometry
        Parameters
        ----------
        query_geom
        buffer_dist

        Returns
        -------
        closure intersecting query_geom
        """
        if buffer_dist != 0:
            query_geom = query_geom.buffer(buffer_dist)
        return lfilter(lambda c: c.shape.intersects(query_geom), self.closures)

    @property
    def closures(self) -> List[Closure]:
        """
        Returns
        -------
        all closures in stretch
        """
        return list(self._closure_map.values())

    def create_pivot(self, origin: Union[CoordType, Point],
                     cargo_dict: Optional[dict] = None) -> Pivot:
        """
        [LOW LEVEL API] create pivot WITHOUT duplicate pivot checking and edge attaching
        Parameters
        ----------
        origin: 2-float-tuple / Coord / Point
        cargo_dict: cargo dict, default to None

        Returns
        -------
        Pivot instance
        """
        pid = str(next(self._pid_gen))
        cargo_dict = cargo_dict or self._default_pivot_cargo_dict
        pivot = Pivot(origin=origin, stretch=self, id_=pid, cargo_dict=cargo_dict)
        self._pivot_map[pid] = pivot
        return pivot

    def create_edge(self) -> 'DanglingEdgeCreator':
        """
        [LOW LEVEL API] enter edge creation mode
        edge creation will avoid to add duplicate edge to stretch
        edge creation will not handle pivot attaching and closure forming
        Returns
        -------
        DanglingEdgeCreator
        """
        from shapely.extension.model.stretch.creator import DanglingEdgeCreator
        return DanglingEdgeCreator(stretch=self)

    def create_closure(self) -> 'ClosureCreator':
        """
        [LOW LEVEL API] enter closure creation mode
        closure creation will avoid to add duplicate closure to stretch
        closure creation will not handle pivot attaching
        Returns
        -------
        ClosureCreator
        """
        from shapely.extension.model.stretch.creator import ClosureCreator
        return ClosureCreator(stretch=self, id_gen=self._cid_gen)

    def remove_dangling_pivots(self) -> None:
        for pivot in self.pivots:
            if pivot.dangling:
                self._pivot_map.pop(pivot.id, None)

    def discard_edge(self, edge: Union[Edge, str], gc: bool = False) -> None:
        """
        [LOW LEVEL API] discard edge from stretch and modify pivots' back ref only. Keep closure untouched.
        discard edge will NOT delete the edge instance and unset its attributes.
        Parameters
        ----------
        edge: edge instance or edge id
        gc: boolean, if True, try to remove dangling pivot. clean the garbage.

        Returns
        -------
        None
        """
        if isinstance(edge, str):
            edge = self.edge(edge)

        if not isinstance(edge, Edge):
            return

        if edge and not edge.deleted:
            self._edge_map.pop(edge.id, None)
            edge_ref = ref(edge)

            if edge_ref in edge.from_pivot._out_edges:
                edge.from_pivot._out_edges.remove(edge_ref)
            if edge_ref in edge.to_pivot._in_edges:
                edge.to_pivot._in_edges.remove(edge_ref)

            if gc:
                if edge.from_pivot.dangling:
                    self._pivot_map.pop(edge.from_pivot.id, None)

                if edge.to_pivot.dangling:
                    self._pivot_map.pop(edge.to_pivot.id, None)

    def delete_edge(self, edge: Union[Edge, str], with_min_cost: bool = True, gc: bool = False) -> None:
        """
        remove edge from stretch, keep corresponding pivots and closure valid
        Parameters
        ----------
        edge: edge instance or edge id
        with_min_cost: boolean, if True, only remove interior if edge is on the interior of a closure; otherwise,
         remove the whole closure
        gc: boolean, if True, remove dangling pivots and edges that have no closure attribute

        Returns
        -------
        None
        """
        if isinstance(edge, str):
            edge = self.edge(edge)

        self.discard_edge(edge, gc=gc)

        if edge.is_interior and with_min_cost:
            interior_idx = first(lambda interior: edge in interior, edge.closure.interiors, return_idx=True)
            if interior_idx is not None:
                for _edge in edge.closure.interiors.pop(interior_idx):
                    _edge.closure = None
                    if gc:
                        self.discard_edge(_edge, gc=gc)

        else:
            self.delete_closure(edge.closure, gc=gc)

        # remove the attribute of edge to avoid the edge being used again
        edge.__del__()  # call __del__ to wipe out the attributes
        assert edge.deleted

    def delete_closure(self, closure: Union[Closure, str], gc: bool = False) -> None:
        """
        remove closure from stretch, remove the back ref of edge correspondingly
        Parameters
        ----------
        closure: closure instance or closure id
        gc: boolean, if True, remove edge without closure attribute and dangling pivots

        Returns
        -------
        None
        """
        if isinstance(closure, str):
            closure = self.closure(closure)

        if closure and not closure.deleted:
            for edge in closure.exterior:
                edge.closure = None
                if gc:
                    self.discard_edge(edge, gc=gc)

            for interior in closure.interiors:
                for edge in interior:
                    edge.closure = None
                    if gc:
                        self.discard_edge(edge, gc=gc)

            self._closure_map.pop(closure.id, None)

            # remove the attribute of closure to avoid the edge being used again
            closure.__del__()
            assert closure.deleted

    def delete_pivot(self, pivot: Union[Pivot, str], gc: bool = False) -> None:
        """
        remove pivot from stretch, handling the invalidity of corresponding edges and closures
        Parameters
        ----------
        pivot: pivot instance or pivot id
        gc: boolean, if True, remove edges without closure attribute and dangling pivots

        Returns
        -------
        None
        """
        if isinstance(pivot, str):
            pivot = self.pivot(pivot)

        if pivot and not pivot.deleted:
            self._pivot_map.pop(pivot.id, None)
            for edge in pivot.in_edges:
                self.delete_edge(edge, gc=gc)

            for edge in pivot.out_edges:
                self.delete_edge(edge, gc=gc)

            # remove the attribute of pivot to avoid the edge being used again
            pivot.__del__()
            assert pivot.deleted

    def add_pivot(self, origin: Union[CoordType, Point],
                  dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                  dist_tol_to_edge: float = MATH_MIDDLE_EPS,
                  cargo_dict: Optional[dict] = None) -> Pivot:
        """
        [MID LEVEL API] create pivot WITH duplicate pivot checking and edge attaching
        Parameters
        ----------
        origin: 2-float-tuple / Coord / Point
        dist_tol_to_edge
        dist_tol_to_pivot
        cargo_dict

        Returns
        -------
        Pivot instance
        """
        point = Point(origin)
        if not point.is_valid or point.is_empty:
            raise ValueError('given origin is not a valid point')

        # check if there is a pivot with same origin
        if existed_pivots := self.pivots_by_query(point, buffer_dist=dist_tol_to_pivot):
            return min(existed_pivots, key=lambda p: p.shape.distance(point))

        # create pivot
        pivot = self.create_pivot(point, cargo_dict=cargo_dict)

        # try to attach pivot to existed edges
        for existed_edge in self.edges_by_query(point, buffer_dist=dist_tol_to_edge):
            if existed_edge in self._edge_map:
                # expand will handle the expansion of existed_edge and its reverse edge
                # which might remove other existed_edges from stretch, thus made existed_edge here garbage
                # so, if an existed_edge don't show up in stretch, just skip the expansion
                existed_edge.expand().by(pivot)  # expand will handle reverse edge expansion

        return pivot

    def add_edge(self, line: LineString,
                 dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                 dist_tol_to_edge: float = MATH_MIDDLE_EPS,
                 cargo_dict: Optional[dict] = None) -> EdgeSeq:
        """
        [MID LEVEL API] create edge with duplicate edge checking and pivot attaching
        NOTICE: it will not guarantee the validity of closures.
        Parameters
        ----------
        line
        dist_tol_to_pivot
        dist_tol_to_edge
        cargo_dict

        Returns
        -------

        """
        if line.is_empty:
            raise ValueError('empty line is not allowed')

        edge_creator = self.create_edge()

        points_on_line: List[Point] = line.ext.decompose(Point).list()

        edges_without_pivot_attaching: List[Edge] = (
            seq(points_on_line)
            .map(lambda p: self.add_pivot(p, dist_tol_to_pivot, dist_tol_to_edge))
            .sliding(2)
            .map(lambda pivot_pair: (edge_creator
                                     .cargo(cargo_dict)
                                     .from_pivot(pivot_pair[0])
                                     .to_pivot(pivot_pair[1])
                                     .create(raise_on_failure=False)))
            .filter(lambda edge: edge is not None)
            .list())

        edges: List[Edge] = []

        for edge in edges_without_pivot_attaching:
            pivots_nearby = self.pivots_by_query(edge.shape, buffer_dist=dist_tol_to_edge)
            pivot_projection_tuples = [(pivot, edge.shape.project(pivot.shape, normalized=True))
                                       for pivot in pivots_nearby]

            pivots = (seq(pivot_projection_tuples)
                      .sorted(itemgetter(1))
                      .drop_while(lambda pivot_projection: pivot_projection[1] == 0)
                      .take_while(lambda pivot_projection: pivot_projection[1] < 1)
                      .map(itemgetter(0))
                      .list())

            edges.extend(edge.expand().by(pivots))

        return EdgeSeq(edges)

    def add_closure(self, polygon: Polygon,
                    dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                    dist_tol_to_edge: float = MATH_MIDDLE_EPS,
                    cargo_dict: Optional[dict] = None) -> Closure:
        """
        [MID LEVEL API] create closure with duplicate closure checking and edge attaching
        Parameters
        ----------
        polygon
        dist_tol_to_pivot
        dist_tol_to_edge
        cargo_dict

        Returns
        -------

        """
        if polygon.is_empty:
            raise ValueError('empty polygon is not allowed')

        polygon = polygon.ext.ccw()
        exterior_seq = self.add_edge(polygon.exterior, dist_tol_to_pivot, dist_tol_to_edge)
        interior_seqs = (seq(polygon.interiors)
                         .map(lambda interior: self.add_edge(interior, dist_tol_to_pivot, dist_tol_to_edge))
                         .list())
        return (self.create_closure()
                .cargo(cargo_dict)
                .exterior(exterior_seq)
                .extend_interiors(interior_seqs)
                .create())

    def split(self, lines: Union[List[LineString], MultiLineString, LineString],
              dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
              dist_tol_to_edge: float = MATH_MIDDLE_EPS,
              closure_strategy: Optional['ClosureStrategy'] = None):

        line: MultiLineString = MultiLineString(flatten(lines).list())
        for closure in self.closures:
            closure.split(line=line,
                          dist_tol_to_pivot=dist_tol_to_pivot,
                          dist_tol_to_edge=dist_tol_to_edge,
                          closure_strategy=closure_strategy)
        return self

    def simplify(self, angle_tol: float = MATH_MIDDLE_EPS,
                 consider_cargo_equality: bool = True,
                 cargo_target: Optional[Callable[[Edge, Edge], Edge]] = None) -> None:
        """
        [MID LEVEL API] simplify the stretch by simplifying closure
        Parameters
        ----------
        angle_tol: angle degree tolerance
        consider_cargo_equality:
        cargo_target

        Returns
        -------
        None
        """
        for closure in self.closures:
            closure.simplify(angle_tol=angle_tol,
                             consider_cargo_equality=consider_cargo_equality,
                             cargo_target=cargo_target)
