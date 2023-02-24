from abc import ABC, abstractmethod

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.model.stretch.stretch_v3 import EdgeSeq, Closure
from shapely.extension.util.func_util import sign
from shapely.geometry import LineString, Point


class BaseOffsetHandler(ABC):
    @abstractmethod
    def offset(self, dist: float) -> LineString:
        raise NotImplementedError

    @abstractmethod
    def attach_endpoints(self, line_after_offset: LineString, dist: float) -> LineString:
        raise NotImplementedError


class OffsetHandler(BaseOffsetHandler):
    def __init__(self, edge_seq: EdgeSeq, closure: Closure):
        self._edge_seq = edge_seq
        self._closure = closure

    def offset(self, dist: float) -> LineString:
        return self._edge_seq.shape.ext.offset(dist)

    def attach_endpoints(self, line_after_offset: LineString, dist: float) -> LineString:
        edge_seq_line = self._edge_seq.shape
        start = edge_seq_line.ext.start()
        end = edge_seq_line.ext.end()
        return LineString([start, *line_after_offset.coords, end])


class NaiveAttachOffsetHandler(OffsetHandler):
    def offset(self, dist: float) -> LineString:
        line_after_offset = super().offset(dist)
        return line_after_offset.ext.prolong().from_ends(self._closure.shape.length)

    def attach_endpoints(self, line_after_offset: LineString, dist: float) -> LineString:
        return line_after_offset


class StrictAttachOffsetHandler(OffsetHandler):
    def offset(self, dist: float) -> LineString:
        closure_poly = self._closure.shape
        line_after_offset: LineString = self._edge_seq.shape.ext.offset(dist)

        if dist < 0:
            # when offset to the outside, we pick the offset line without any extension as result
            return line_after_offset

        if (line_after_offset.ext.start().disjoint(closure_poly)
                and line_after_offset.ext.end().disjoint(closure_poly)
                and not line_after_offset.intersects(closure_poly)):
            # when the entire line is outside the closure, we pick the extended line as result
            return line_after_offset.ext.prolong().from_ends(closure_poly.length)

        # when at least 1 endpoint is inside the closure
        offset_line_inside = line_after_offset.intersection(closure_poly)
        start_point = offset_line_inside.ext.start()
        end_point = offset_line_inside.ext.end()

        query_line_for_new_end_point = offset_line_inside.ext.prolong().from_tail(closure_poly.length)
        nearest_point_to_end_point = (query_line_for_new_end_point
                                      .ext.buffer().single_sided().rect(-(dist + MATH_MIDDLE_EPS * sign(dist > 0)))
                                      .intersection(closure_poly.boundary)
                                      .ext.decompose(Point)
                                      .filter(lambda pt: pt != start_point)
                                      .min_by(end_point.distance))
        new_end_point = offset_line_inside.ext.projected_point(nearest_point_to_end_point)

        query_line_for_new_start_point = offset_line_inside.ext.prolong().from_head(closure_poly.length)
        nearest_point_to_start_point = (query_line_for_new_start_point
                                        .ext.buffer().single_sided().rect(-(dist + MATH_MIDDLE_EPS * sign(dist > 0)))
                                        .intersection(closure_poly.boundary)
                                        .ext.decompose(Point)
                                        .filter(lambda pt: pt != end_point)
                                        .min_by(start_point.distance))
        new_start_point = offset_line_inside.ext.projected_point(nearest_point_to_start_point)
        return LineString([new_start_point, new_end_point])

    def attach_endpoints(self, line_after_offset: LineString, dist: float) -> LineString:
        if dist < 0:
            return LineString([self._edge_seq.shape.ext.start(),
                               *line_after_offset.coords,
                               self._edge_seq.shape.ext.end()])

        closure_poly = self._closure.shape
        if (line_after_offset.ext.start().disjoint(closure_poly)
                and line_after_offset.ext.end().disjoint(closure_poly)
                and not line_after_offset.intersects(closure_poly)):
            return line_after_offset

        query_line_for_start_attachment = line_after_offset.ext.prolong().from_head(self._closure.shape.length)
        nearest_point_to_start = (query_line_for_start_attachment
                                  .ext.buffer().single_sided().rect(-(dist + MATH_MIDDLE_EPS * sign(dist > 0)))
                                  .intersection(self._closure.shape.boundary)
                                  .ext.decompose(Point)
                                  .min_by(line_after_offset.ext.start().distance))

        query_line_for_end_attachment = line_after_offset.ext.prolong().from_tail(self._closure.shape.length)
        nearest_point_to_end = (query_line_for_end_attachment
                                .ext.buffer().single_sided().rect(-(dist + MATH_MIDDLE_EPS * sign(dist > 0)))
                                .intersection(self._closure.shape.boundary)
                                .ext.decompose(Point)
                                .min_by(line_after_offset.ext.end().distance))

        return LineString([nearest_point_to_start, *list(line_after_offset.coords), nearest_point_to_end])
