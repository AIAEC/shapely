from collections import deque
from operator import attrgetter
from typing import Optional, List, Set, Dict, Deque, Callable

from toolz import curry

from shapely.extension.functional import seq
from shapely.extension.model.angle import Angle
from shapely.extension.model.stretch.stretch_v3 import Edge, EdgeSeq
from shapely.extension.util.func_util import lfilter


class ClosureStrategy:
    """
    strategy to form closure
    Basically contains methods to search edge sequence
    """

    @staticmethod
    @curry
    def edge_to_base_ccw_angle(edge: Edge, base_angle: Angle) -> float:
        if edge.shape.length == 0:
            return 0
        angle = edge.shape.ext.angle().rotating_angle(base_angle, direct='ccw').degree

        if angle == 0:
            return 360  # make sure the edge with same angle to base_angle is the last to consider

        return angle

    @classmethod
    def next_edge_score_func(cls, cur_edge: Edge) -> Callable[[Edge], float]:
        reverse_edge_angle: Angle = cur_edge.shape.ext.reverse().ext.angle()
        return cls.edge_to_base_ccw_angle(base_angle=reverse_edge_angle)

    @classmethod
    def next_edge(cls, edge: Edge) -> Optional[Edge]:
        # TODO: optimize this method based on vector operation
        if not edge.shape.is_valid:
            return None

        out_edges = edge.to_pivot.out_edges

        if len(out_edges) == 1:  # for speed up
            return out_edges[0]

        out_edges = lfilter(lambda e: (e is not edge
                                       and e is not edge.reverse
                                       and isinstance(e, Edge)
                                       and e.shape.is_valid),
                            out_edges)

        return min(out_edges, key=cls.next_edge_score_func(edge), default=None)

    @staticmethod
    @curry
    def base_to_edge_reverse_ccw_angle(edge: Edge, base_angle: Angle):
        if edge.shape.length == 0:
            return 0

        angle = base_angle.rotating_angle(edge.shape.ext.reverse().ext.angle()).degree

        if angle == 0:
            return 360  # make sure the edge with same angle to base_angle is the last to consider

        return angle

    @classmethod
    def prev_edge_score_func(cls, edge: Edge) -> Callable[[Edge], float]:
        edge_angle: Angle = edge.shape.ext.angle()
        return cls.base_to_edge_reverse_ccw_angle(base_angle=edge_angle)

    @classmethod
    def prev_edge(cls, edge: Edge) -> Optional[Edge]:
        # TODO: optimize this method based on vector operation
        if not edge.shape.is_valid:
            return None

        in_edges = edge.from_pivot.in_edges

        if len(in_edges) == 1:  # for speed up
            return in_edges[0]

        in_edges = lfilter(lambda e: (e is not edge
                                      and e is not edge.reverse
                                      and isinstance(e, Edge)
                                      and e.shape.is_valid),
                           in_edges)

        return min(in_edges, key=cls.prev_edge_score_func(edge), default=None)

    @classmethod
    def consecutive_edges(cls, edge: Edge, candidate_edges: Optional[Set[Edge]] = None) -> EdgeSeq:
        assert isinstance(edge, Edge)

        edges = [edge]
        seen = set(edges)

        if candidate_edges is None:
            candidate_edges = set(edge.stretch.edges)

        if edge not in candidate_edges:
            return EdgeSeq([])

        while (next_edge := edge.next()) and (next_edge not in seen):
            if next_edge not in candidate_edges:
                break

            edges.append(next_edge)
            seen.add(next_edge)
            edge = next_edge

        return EdgeSeq(edges)

    @classmethod
    def sort_edges_by_chain(cls, edges: List[Edge]) -> List[Edge]:
        """
        Sort the edges to make a chain list of edges.
        If given edges cannot form a chain, raise ValueError
        CAUTION: given edges either form a closed ring or a chain without self intersection, otherwise the order is not
        deterministic. Self intersection excludes case of back and forth edges.
        Parameters
        ----------
        edges: list of edges

        Returns
        -------
        list of sorted edges
        """
        if len(edges) <= 1:
            return edges

        from_pids_map: Dict[str, List[Edge]] = seq(edges).group_by(attrgetter('from_pid')).dict()
        to_pid_map: Dict[str, List[Edge]] = seq(edges).group_by(attrgetter('to_pid')).dict()

        edge_deque: Deque[Edge] = deque([edges[0]])
        seen: Set[Edge] = set(edge_deque)

        while next_edges := from_pids_map.get(edge_deque[-1].to_pid, []):
            next_edge = min(next_edges, key=cls.next_edge_score_func(edge_deque[-1]))
            next_edges.remove(next_edge)
            if next_edge not in seen:
                edge_deque.append(next_edge)
                seen.add(next_edge)

        while prev_edges := to_pid_map.get(edge_deque[0].from_pid, []):
            prev_edge = min(prev_edges, key=cls.prev_edge_score_func(edge_deque[0]))
            prev_edges.remove(prev_edge)
            if prev_edge not in seen:
                edge_deque.appendleft(prev_edge)
                seen.add(prev_edge)

        if len(edge_deque) != len(edges):
            raise ValueError(
                f'given {edges}, sorted edges are {list(edge_deque)}, probably given edges cannot form a chain')

        return list(edge_deque)
