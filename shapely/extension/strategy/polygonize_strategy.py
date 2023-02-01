from abc import ABC, abstractmethod
from typing import List

from shapely.extension.constant import LARGE_EPS
from shapely.extension.functional import seq
from shapely.extension.util.flatten import flatten
from shapely.extension.util.prolong import prolong
from shapely.geometry import LineString, Polygon, LinearRing
from shapely.ops import polygonize as shapely_polygonize, unary_union


class PolygonizeStrategy(ABC):
    @abstractmethod
    def compose(self, line_segments: List[LineString]) -> List[Polygon]:
        raise NotImplementedError


class ShapelyPolygonizeStrategy(PolygonizeStrategy):
    def compose(self, line_segments: List[LineString]) -> List[Polygon]:
        return [*shapely_polygonize(line_segments)]


class ConvexHullStrategy(PolygonizeStrategy):
    def __init__(self, math_eps: float = LARGE_EPS, convex_hull_overlapping_ratio_threshold=0.99):
        """
        Parameters
        ----------
        math_eps: math err tolerance
        convex_hull_overlapping_ratio_threshold: if convex hull boundary and polyline's overlapping ratio larger
            than this ratio, consider its convex hull as found polygon
        """
        self._math_eps = math_eps
        self._convex_hull_overlapping_ratio_threshold = convex_hull_overlapping_ratio_threshold

    def compose(self, line_segments: List[LineString]) -> List[Polygon]:
        polygon = unary_union(line_segments).convex_hull
        if not isinstance(polygon, Polygon):
            return []

        buffered_line_segments = unary_union(line_segments)
        overlapped_outline = buffered_line_segments.intersection(polygon.exterior.buffer(self._math_eps * 2))

        result: List[Polygon] = []
        if overlapped_outline.length / sum(
                segment.length for segment in line_segments) > self._convex_hull_overlapping_ratio_threshold:
            result.append(polygon)
        return result


class MouldStrategy(PolygonizeStrategy):
    def __init__(self, mould_cutting_buffer: float = 1e-7,
                 max_line_gap: float = LARGE_EPS):
        """
        Parameters
        ----------
        mould_cutting_buffer: line buffer distance
        max_line_gap: max prolong length for lines to prevent disconnected lines
        """
        self._mould_cutting_buffer = mould_cutting_buffer
        self._prolong_length = max_line_gap

    def compose(self, line_segments: List[LineString]) -> List[Polygon]:
        board = unary_union(line_segments).envelope.buffer(1 + self._prolong_length)
        cutting = (unary_union(seq(line_segments)
                               .filter(lambda line: line.length > 0)
                               .map(lambda line: prolong(line=line,
                                                         front_prolong_len=self._prolong_length,
                                                         end_prolong_len=self._prolong_length))
                               .map(lambda line: line.buffer(self._mould_cutting_buffer))
                               .to_list()))
        pieces = flatten(board.difference(cutting)).to_list()
        return (seq(pieces)
                .filter(lambda piece: piece.envelope.area < board.area)
                .filter(lambda geom: isinstance(geom, Polygon) and geom.is_valid and not geom.is_empty)
                .to_list())


class ClosingEndPointsStrategy(PolygonizeStrategy):
    def compose(self, line_segments: List[LineString]) -> List[Polygon]:
        return (seq(line_segments)
                .map(lambda line: self.close_linestring(line))
                .map(lambda ring: Polygon(ring))
                .filter(lambda p: p.ext.is_("valid", "not_empty"))
                .to_list())

    def close_linestring(self, line: LineString) -> LinearRing:
        if isinstance(line, LineString):
            coords = list(line.coords)
            return LinearRing(coords + [coords[0]])
        elif isinstance(line, LinearRing):
            return line

        raise NotImplementedError(f"only support linestring, given {type(line)}")
