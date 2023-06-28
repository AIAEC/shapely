from typing import Union, List, Optional

from shapely.extension.constant import MATH_MIDDLE_EPS, COMPARE_EPS, STRETCH_EPS
from shapely.extension.functional import seq
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.stretch.closure_strategy import ClosureStrategy
from shapely.extension.model.stretch.creator import ClosureReconstructor
from shapely.extension.model.stretch.offset_strategy import AngleAttachOffsetHandler
from shapely.extension.model.stretch.stretch_v3 import Edge, EdgeSeq, Closure
from shapely.extension.model.vector import Vector
from shapely.extension.util.func_util import group
from shapely.extension.util.iter_util import first
from shapely.geometry import LineString, Polygon, Point


class Offset:
    def __init__(self, edge: Union[Edge, EdgeSeq], offset_handler_cls=None):
        self._edge_seq = edge
        self._edge_seq_shape = self._edge_seq.shape
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

        self._offset_handler_cls = offset_handler_cls or AngleAttachOffsetHandler
        self._shape_offset_strategy = self._offset_handler_cls(edge_seq=self._edge_seq, closure=self._closure)

    def query_the_offset_edge_seq(self, line_after_offset: LineString) -> List[EdgeSeq]:
        if not line_after_offset.is_valid or line_after_offset.is_empty:
            return []

        # since offset might cause deformation, we need to make query distance larger than MATH_MIDDLE_EPS
        offset_line_region = line_after_offset.ext.buffer().rect(COMPARE_EPS / 10)
        edges: List[Edge] = (
            seq(self._stretch.edges_by_query(offset_line_region))
            .filter(lambda e: e.shape.intersection(offset_line_region).length > max(e.shape.length / 2,
                                                                                    2 * COMPARE_EPS / 10))
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
               dist_tol_to_pivot: float = STRETCH_EPS,
               dist_tol_to_edge: float = STRETCH_EPS) -> List[EdgeSeq]:
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
                                     line_after_offset=line_after_offset,
                                     offset_dist=dist,
                                     inclusive_space=self._closure.shape,
                                     union_to_closure=union_to_closure,
                                     dist_tol_to_pivot=dist_tol_to_pivot,
                                     dist_tol_to_edge=dist_tol_to_edge)

        # case 3: offset exterior into outer space
        elif self._edge.is_exterior and dist < 0:
            self.outer_offset_helper(line_after_offset=line_after_offset,
                                     offset_dist=dist,
                                     exclusive_space=None,
                                     dist_tol_to_pivot=dist_tol_to_pivot,
                                     dist_tol_to_edge=dist_tol_to_edge)

        # case 4: offset interior into outer space
        elif self._edge.is_interior and dist < 0:
            self.outer_offset_helper(line_after_offset=line_after_offset,
                                     offset_dist=dist,
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
                            line_after_offset: LineString,
                            offset_dist: float,
                            inclusive_space: Polygon,
                            union_to_closure: Optional[Closure] = None,
                            dist_tol_to_pivot: float = STRETCH_EPS,
                            dist_tol_to_edge: float = STRETCH_EPS) -> None:
        """

        Parameters
        ----------
        line_after_attach
        line_after_offset
        offset_dist
        inclusive_space: space that the line_after_attach must be inside
        union_to_closure
        dist_tol_to_pivot
        dist_tol_to_edge

        Returns
        -------

        """
        inclusive_space_boundary = inclusive_space.boundary
        segment_seq = inclusive_space.intersection(line_after_attach).ext.decompose(StraightSegment)
        segments_inside: List[StraightSegment] = (segment_seq
                                                  .map(lambda seg: seg.difference(inclusive_space_boundary))
                                                  .flat_map(lambda seg: seg.ext.flatten(LineString))
                                                  .list())
        segments_on_boundary: List[StraightSegment] = (segment_seq
                                                       .map(lambda seg: seg.intersection(inclusive_space_boundary))
                                                       .flat_map(lambda seg: seg.ext.flatten(LineString))
                                                       .list())

        if not (segments_inside + segments_on_boundary):
            if union_to_closure is None:
                # remove the target closure and its edges
                self._stretch.delete_closure(self._closure, gc=True)
            else:
                union_to_closure.union(self._closure)  # union_to_closure as the primary for cargo
            return

        new_edges: List[Edge] = []

        for segment_on_boundary in segments_on_boundary:
            # segment is on the boundary of inclusive_space, adding endpoints of segment as pivots is proper to
            # form new closures.
            # adding double edge can cause invalid closure, as shows below:
            #     overlap
            # ┌───────┐       ┌───┐◄──►
            # │     ▲ │       │   │
            # │     │ │       │   │
            # │   ┌─┴─┘       │   │
            # └───┘           └───┘
            pivot0 = self._stretch.add_pivot(segment_on_boundary.ext.start(),
                                             dist_tol_to_pivot=dist_tol_to_pivot,
                                             dist_tol_to_edge=dist_tol_to_edge)
            pivot1 = self._stretch.add_pivot(segment_on_boundary.ext.end(),
                                             dist_tol_to_pivot=dist_tol_to_pivot,
                                             dist_tol_to_edge=dist_tol_to_edge)
            possible_edge0 = self._stretch.edge(f'({pivot0.id}, {pivot1.id})')
            possible_edge1 = self._stretch.edge(f'({pivot1.id}, {pivot0.id})')
            if edge := first(lambda edge: bool(edge) and edge.closure is self._closure,
                             [possible_edge0, possible_edge1]):
                new_edges.append(edge)

        for segment_inside in segments_inside:
            # segment is in the interior space of inclusive_space, add double edges of segment
            # to form new closures
            new_edges.extend(self._stretch.add_edge(line=segment_inside,
                                                    dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge))
            new_edges.extend(self._stretch.add_edge(line=segment_inside.ext.reverse(),
                                                    dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge))

        closure_edges = self._closure.edges

        # put delete closure ahead of creation of new closure, to avoid deletion closure reset edges' closure ref when
        # new closures hold the same edge as the deleted closure does
        self._stretch.delete_closure(self._closure, gc=False)

        new_closures: List[Closure] = (ClosureReconstructor(stretch=self._stretch)
                                       .cargo(self._closure.cargo.data)
                                       .from_edges(new_edges + closure_edges)
                                       .reconstruct(dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge))

        # inherit cargo of pivots and edges before deleting or merging closure
        self.inherit_pivot_cargo(line_after_offset=line_after_offset, offset_dist=offset_dist)
        self.inherit_edge_cargo(line_after_offset=line_after_offset, offset_dist=offset_dist)

        disposal_closure = max(new_closures,
                               key=lambda closure: self._edge_seq_shape.intersection(closure.shape).length)
        assert isinstance(disposal_closure, Closure)  # must have this closure

        if union_to_closure is None:
            # remove the target closure and its edges
            self._stretch.delete_closure(disposal_closure, gc=True)
        else:
            union_to_closure.union(disposal_closure)  # union_to_closure as the primary for cargo

    def outer_offset_helper(self, line_after_offset: LineString,
                            offset_dist: float,
                            exclusive_space: Optional[Polygon] = None,
                            dist_tol_to_pivot: float = STRETCH_EPS,
                            dist_tol_to_edge: float = STRETCH_EPS) -> None:
        """

        Parameters
        ----------
        line_after_offset
        offset_dist
        exclusive_space
        dist_tol_to_pivot
        dist_tol_to_edge

        Returns
        -------

        """
        new_closure_placeholder = line_after_offset.union(self._edge_seq.shape).minimum_rotated_rectangle
        if exclusive_space:
            new_closure_placeholder = new_closure_placeholder.difference(exclusive_space)

        union_to_closure = self._closure

        for new_closure_poly in new_closure_placeholder.ext.flatten(Polygon).list():
            new_closure = self._stretch.add_closure(new_closure_poly,
                                                    dist_tol_to_pivot=dist_tol_to_pivot,
                                                    dist_tol_to_edge=dist_tol_to_edge,
                                                    cargo_dict=self._closure.cargo.data)

            self.inherit_edge_cargo(line_after_offset=line_after_offset, offset_dist=offset_dist)
            self.inherit_pivot_cargo(line_after_offset=line_after_offset, offset_dist=offset_dist)

            # if union failed, return (union_to_closure, new_closure), thus union_to_closure remains unchanged
            # if union success, return list of new closures with only one element, thus union_to_closure is updated
            # union_to_closure is the primary closure
            union_to_closure, *_ = union_to_closure.union(new_closure)

    def inherit_pivot_cargo(self, line_after_offset: LineString, offset_dist: float):
        line_before_offset = line_after_offset.ext.offset(-offset_dist)
        origin_points = line_before_offset.ext.decompose(Point).list()
        cur_points = line_after_offset.ext.decompose(Point).list()
        assert len(origin_points) == len(cur_points)

        for origin_point, current_point in zip(origin_points, cur_points):
            origin_pivot = self._stretch.find_pivot(origin_point, buffer_dist=MATH_MIDDLE_EPS)
            current_pivot = self._stretch.find_pivot(current_point, buffer_dist=MATH_MIDDLE_EPS)
            if origin_pivot and current_pivot:
                current_pivot.cargo.update(origin_pivot.cargo.data)

    def inherit_edge_cargo(self, line_after_offset: LineString, offset_dist: float):
        line_before_offset = line_after_offset.ext.offset(-offset_dist)
        segments_before_offset = line_before_offset.ext.decompose(StraightSegment).list()
        segments_after_offset = line_after_offset.ext.decompose(StraightSegment).list()
        assert len(segments_before_offset) == len(segments_after_offset)

        for segment_before_offset, segment_after_offset in zip(segments_before_offset, segments_after_offset):
            origin_edge = self._stretch.find_edge(segment_before_offset, buffer_dist=MATH_MIDDLE_EPS,
                                                  strict_angle_match=True)
            current_edge = self._stretch.find_edge(segment_after_offset, buffer_dist=MATH_MIDDLE_EPS,
                                                   strict_angle_match=True)
            if origin_edge and current_edge:
                current_edge.cargo.update(origin_edge.cargo.data)

                if origin_edge.reverse and current_edge.reverse:
                    current_edge.reverse.cargo.update(origin_edge.reverse.cargo.data)
