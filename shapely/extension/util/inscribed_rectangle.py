from math import isclose
from operator import attrgetter
from typing import List, Literal, Optional

from shapely.extension.constant import MATH_MIDDLE_EPS
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
        if self._polygon.interiors:
            raise NotImplementedError("InscribedRectangle does not support polygon with holes")

    def by_straight_line(self, line: LineString, towards: Literal['left', 'right', 'both'] = 'both') -> List[Rect]:
        line_inside: LineString = line.ext.prolong().from_ends(self._polygon.length)

        if not line_inside:
            return []

        inscribed_rects: List[Rect] = []

        end_lines = self._end_lines(line_inside, 'left') + self._end_lines(line_inside, 'right')
        if towards != 'both':
            end_lines = self._end_lines(line_inside, towards)

        for end_line in end_lines:

            if rectangle := self._inner_rectangle(line_inside, end_line):
                inscribed_rects.append(rectangle)

        return inscribed_rects

    def _end_lines(self, start_line: LineString, searching_side: Literal['left', 'right'] = 'left') -> List[LineString]:
        _sign = sign(searching_side == 'left')
        query_region = start_line.ext.rbuf(self._polygon.length * _sign, single_sided=True)
        end_lines = (query_region.intersection(self._polygon.exterior)
                     .ext.decompose(Point)
                     .map(lambda seg: seg.distance(start_line))
                     .distinct()
                     .filter_not(lambda dist: isclose(dist, 0))
                     .map(lambda dist: start_line.ext.offset(dist * _sign))
                     .list())
        return end_lines

    def _inner_rectangle(self, start_line: LineString,
                         end_line: LineString) -> Optional[Rect]:
        start_line = start_line.intersection(self._polygon).ext.longest_piece()
        end_line = end_line.intersection(self._polygon).ext.longest_piece()

        if not (start_line and end_line and isinstance(start_line, LineString) and isinstance(end_line, LineString)):
            return None

        obstacles = (start_line.union(end_line)
                     .minimum_rotated_rectangle
                     .ext.rbuf(-MATH_MIDDLE_EPS)
                     .difference(self._polygon))

        intervals: List[Interval] = (start_line
                                     .ext.projection_by(obstacles)
                                     .negative_intervals())

        if not intervals:
            return None

        interval = max(intervals, key=attrgetter('length'))
        start_segment = start_line.ext.substring(interval)
        opposite_segments = end_line.ext.projection_by(start_segment).segments
        end_segment = max(opposite_segments, key=attrgetter('length'), default=None)

        if end_segment:
            return Rect(start_segment.union(end_segment).minimum_rotated_rectangle.ext.ccw())

        return None
