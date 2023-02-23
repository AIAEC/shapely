from typing import Union, List, Optional

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.functional import seq
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
from shapely.extension.model.stretch.creator import ClosureReconstructor
from shapely.extension.model.stretch.offset_strategy import OffsetHandler
from shapely.extension.model.stretch.stretch_v3 import Edge, EdgeSeq, Closure
from shapely.extension.model.vector import Vector
from shapely.extension.util.func_util import group
from shapely.extension.util.iter_util import first
from shapely.geometry import LineString, Polygon


class Offset:
    def __init__(self, edge: Union[Edge, EdgeSeq], offset_handler_cls=None):
        self._edge_seq = edge
        if isinstance(edge, Edge):
            self._edge_seq = EdgeSeq([edge])

        closures = self._edge_seq.closures
        assert len(set(closures)) == 1, 'offset only works for edges that belongs to one closure'
        self._closure = closures[0]

        self._stretch = self._closure.stretch
        assert self._stretch, 'offset only works for edges that belongs to a stretch'

        reverse_closures = list(set(edge.reverse_closure for edge in self._edge_seq))
        error_info = ('offset only accepts that reverse edges should belong to one closure or no closure; '
                      'if not, please offset each edge one by one')
        assert len(reverse_closures) == 1, error_info

        self._edge = self._edge_seq[0]

        self._offset_handler_cls = offset_handler_cls or OffsetHandler
        self._shape_offset_strategy = self._offset_handler_cls(edge_seq=self._edge_seq, closure=self._closure)

    def query_the_offset_edge_seq(self, line_after_offset: LineString) -> List[EdgeSeq]:
        offset_line_region = line_after_offset.ext.buffer().rect(MATH_MIDDLE_EPS)
        edges: List[Edge] = (seq(self._stretch.edges_by_query(offset_line_region))
                             .filter(lambda e: e.shape.intersection(offset_line_region).length > 2 * MATH_MIDDLE_EPS)
                             .list())
        edge_pairs: List[List[Edge]] = group(lambda e0, e1: e0.reverse == e1, edges)

        direction = Vector.from_endpoints_of(line_after_offset)

        def pick_edge(edge_pair):
            if len(edge_pair) == 1:
                return edge_pair[0]

            edge = first(lambda e: Vector.from_endpoints_of(e.shape).dot(direction) > 0, edge_pair)
            assert isinstance(edge, Edge)
            return edge

        edges = [pick_edge(edge_pair) for edge_pair in edge_pairs]
        edges_groups: List[List[Edge]] = group(lambda e0, e1: e0.to_pid == e1.from_pid, edges)

        return [EdgeSeq(ClosureStrategy.sort_edges_by_chain(_edges)) for _edges in edges_groups]

    def offset(self, dist: float,
               dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
               dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> List[EdgeSeq]:
        """

        Parameters
        ----------
        dist: if positive, offset to current edge's left, otherwise to right
        dist_tol_to_edge
        dist_tol_to_pivot

        Returns
        -------

        """
        if dist == 0:
            return [self._edge_seq]

        # there are 4 cases:
        # 1. exterior edge, offset to inner space(offset towards left side), which is shrinking the closure
        # 2. interior edge, offset to inner space(offset towards left side), which is shrinking the closure
        # 3. exterior edge, offset to outer space(offset towards right side), which is expanding the closure
        # 4. interior edge, offset to outer space, the hole(offset towards right side), which is expanding the closure

        # special condition of case 3: which can be transferred into case 1
        # the out going offset of origin edge is equal to the inner going offset of reverse edge
        # only if reverse edge has bound to a closure
        if dist < 0 and self._edge.reverse_closure:
            return (Offset(edge=self._edge.reverse, offset_handler_cls=self._offset_handler_cls)
                    .offset(dist=-dist, dist_tol_to_pivot=dist_tol_to_pivot, dist_tol_to_edge=dist_tol_to_edge))

        line_after_offset: LineString = self._shape_offset_strategy.offset(dist=dist)
        line_after_attach: LineString = self._shape_offset_strategy.attach_endpoints(line_after_offset, dist=dist)

        # case 1 & 2: offset exterior / interior into inner space
        if dist > 0:
            union_to_closure = self._edge.reverse_closure
            self.inner_offset_helper(line_after_attach=line_after_attach,
                                     inclusive_space=self._closure.shape,
                                     union_to_closure=union_to_closure,
                                     dist_tol_to_pivot=dist_tol_to_pivot,
                                     dist_tol_to_edge=dist_tol_to_edge)

        # case 3: offset exterior into outer space
        elif self._edge.is_exterior and dist < 0:
            self.outer_offset_helper(line_after_offset=line_after_offset,
                                     exclusive_space=None,
                                     dist_tol_to_pivot=dist_tol_to_pivot,
                                     dist_tol_to_edge=dist_tol_to_edge)

        # case 4: offset interior into outer space
        elif self._edge.is_interior and dist < 0:
            self.outer_offset_helper(line_after_offset=line_after_offset,
                                     exclusive_space=self._closure.shape,
                                     dist_tol_to_pivot=dist_tol_to_pivot,
                                     dist_tol_to_edge=dist_tol_to_edge)

        offset_edge_seqs: List[EdgeSeq] = self.query_the_offset_edge_seq(line_after_offset)

        # collection garbage and make current instance invalid
        self._edge = None
        self._edge_seq = None
        self._closure = None
        self._shape_offset_strategy = None

        return offset_edge_seqs

    def inner_offset_helper(self, line_after_attach: LineString,
                            inclusive_space: Polygon,
                            union_to_closure: Optional[Closure] = None,
                            dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                            dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> None:
        """

        Parameters
        ----------
        line_after_attach
        inclusive_space: space that the line_after_attach must be inside
        union_to_closure
        dist_tol_to_pivot
        dist_tol_to_edge

        Returns
        -------

        """
        segments: List[StraightSegment] = (inclusive_space.intersection(line_after_attach)
                                           .ext.decompose(StraightSegment)
                                           .list())
        if not segments:
            if union_to_closure is None:
                # remove the target closure and its edges
                self._stretch.delete_closure(self._closure, gc=True)
            else:
                self._closure, *_ = self._closure.union(union_to_closure)
            return

        new_edges: List[Edge] = []
        for segment in segments:
            new_edges.extend(self._stretch.add_edge(line=segment,
                                                    dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge))
            new_edges.extend(self._stretch.add_edge(line=segment.ext.reverse(),
                                                    dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge))

        closure_edges = self._closure.edges

        # put delete closure ahead of creation of new closure, to avoid deletion closure reset edges' closure ref when
        # new closures hold the same edge as the deleted closure does
        self._stretch.delete_closure(self._closure, gc=False)

        new_closures: List[Closure] = (ClosureReconstructor(stretch=self._stretch)
                                       .from_edges(new_edges + closure_edges)
                                       .reconstruct(dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge))

        target_closure = first(lambda closure: self._edge in closure.exterior, new_closures)
        assert isinstance(target_closure, Closure)  # must have target closure

        if union_to_closure is None:
            # remove the target closure and its edges
            self._stretch.delete_closure(target_closure, gc=True)
        else:
            self._closure, *_ = target_closure.union(union_to_closure)

    def outer_offset_helper(self, line_after_offset: LineString,
                            exclusive_space: Optional[Polygon] = None,
                            dist_tol_to_pivot: float = MATH_MIDDLE_EPS,
                            dist_tol_to_edge: float = MATH_MIDDLE_EPS) -> None:
        new_closure_placeholder = line_after_offset.union(self._edge_seq.shape).minimum_rotated_rectangle
        if exclusive_space:
            new_closure_placeholder = new_closure_placeholder.difference(exclusive_space)

        union_to_closure = self._closure

        for new_closure_poly in new_closure_placeholder.ext.flatten(Polygon).list():
            new_closure = self._stretch.add_closure(new_closure_poly,
                                                    dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge)

            # if union failed, return (union_to_closure, new_closure), thus union_to_closure remains unchanged
            # if union success, return list of new closures with only one element, thus union_to_closure is updated
            union_to_closure, *_ = union_to_closure.union(new_closure)
