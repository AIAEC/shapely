from collections import deque
from typing import Optional, List, Set

from shapely.extension.model.angle import Angle
from shapely.extension.model.stretch.stretch_v3 import Edge, EdgeSeq
from shapely.extension.util.func_util import lfilter


class ClosureStrategy:
    """
    strategy to form closure
    Basically contains methods to search edge sequence
    """

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

        reverse_edge_angle: Angle = edge.shape.ext.reverse().ext.angle()

        def other_ccw_rotating_angle_to_inversion_of_given_edge(other_edge: Edge):
            if other_edge.shape.length == 0:
                return 0
            angle = other_edge.shape.ext.angle().rotating_angle(reverse_edge_angle, direct='ccw').degree

            if angle == 0:
                return 360  # make sure the edge with same angle as reverse_edge is the last to consider

            return angle

        return min(out_edges, key=other_ccw_rotating_angle_to_inversion_of_given_edge, default=None)

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

        edge_angle: Angle = edge.shape.ext.angle()

        def given_edge_rotating_to_reverse_of_other(other_edge: Edge):
            if other_edge.shape.length == 0:
                return 0

            angle = edge_angle.rotating_angle(other_edge.shape.ext.reverse().ext.angle()).degree

            if angle == 0:
                return 360  # make sure the edge with same angle as reverse_edge is the last to consider

            return angle

        return min(in_edges, key=given_edge_rotating_to_reverse_of_other, default=None)

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
        Parameters
        ----------
        edges: list of edges

        Returns
        -------
        list of sorted edges
        """
        if len(edges) <= 1:
            return edges

        head = min(edges, key=lambda e: e.id)
        edge_set = set(edges).difference([head])

        queue = deque([head])
        cur = head
        while ((next_ := cur.next(cls))
               and (next_ in edge_set)
               and (next_ is not head)):
            queue.append(next_)
            edge_set.remove(next_)
            cur = next_

        if edge_set:
            cur = head
            while ((last := cur.prev(cls))
                   and (last in edge_set)
                   and (last is not head)):
                queue.appendleft(last)
                edge_set.remove(last)
                cur = last

        if len(queue) != len(edges):
            raise ValueError('Edges are not connected')

        return list(queue)

