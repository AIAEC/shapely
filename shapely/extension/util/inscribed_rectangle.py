from math import isclose
from operator import attrgetter
from typing import List, Literal

from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.geometry.empty import EMPTY_GEOM
from shapely.extension.geometry.rect import Rect
from shapely.extension.model.interval import Interval
from shapely.extension.util.func_util import sign
from shapely.geometry import Polygon, LineString, Point


class InscribedRectangle:
    def __init__(self, polygon: Polygon):
        """
        Parameters
        ----------
        polygon: given polygon
        """
        self._polygon = polygon

    def by_straight_line(self, start_line: LineString, towards: Literal['left', 'right', 'both'] = 'both') -> List[Rect]:
        if not start_line:
            return []

        inscribed_rects: List[Rect] = []

        end_lines = self._end_lines(start_line, 'left') + self._end_lines(start_line, 'right')
        if towards != 'both':
            end_lines = self._end_lines(start_line, towards)

        for end_line in end_lines:
            if rectangles := self._inner_rectangle(start_line, end_line):
                inscribed_rects.extend(rectangles)

        return inscribed_rects

    def _end_lines(self, start_line: LineString, searching_side: Literal['left', 'right'] = 'left') -> List[LineString]:
        _sign = sign(searching_side == 'left')
        query_region = start_line.ext.rbuf(self._polygon.length * _sign, single_sided=True)
        end_lines = (query_region.intersection(self._polygon)
                     .ext.flatten(Polygon)
                     .min_by(start_line.distance, default=EMPTY_GEOM)
                     .ext.decompose(Point)
                     .map(lambda point: point.distance(start_line))
                     .distinct()
                     .filter_not(lambda dist: isclose(dist, 0, abs_tol=MATH_MIDDLE_EPS))
                     .map(lambda dist: start_line.ext.offset(dist * _sign))
                     .list())
        return end_lines

    def _inner_rectangle(self, start_line: LineString,
                         end_line: LineString) -> List[Rect]:
        if not (start_line and end_line and isinstance(start_line, LineString) and isinstance(end_line, LineString)):
            return []

        obstacles = (start_line.union(end_line)
                     .minimum_rotated_rectangle
                     .ext.rbuf(-MATH_MIDDLE_EPS)
                     .difference(self._polygon))

        intervals: List[Interval] = (start_line
                                     .ext.projection_by(obstacles)
                                     .negative_intervals())

        if not intervals:
            return []

        result: List[Rect] = []

        for interval in intervals:
            start_segment = start_line.ext.substring(interval)
            opposite_segments = end_line.ext.projection_by(start_segment).segments
            end_segment = max(opposite_segments, key=attrgetter('length'), default=None)

            if end_segment and end_segment.length > 0:
                result.append(Rect(start_segment.union(end_segment).minimum_rotated_rectangle.ext.ccw()))

        return result
