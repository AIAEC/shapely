from typing import Union, List

from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType, Num
from shapely.geometry import Point, LineString


def prolong(line: LineString,
            front_prolong_len: float = 0,
            end_prolong_len: float = 0) -> LineString:
    """
    延长线的两端
    Parameters
    ----------
    line
    front_prolong_len
    end_prolong_len

    Returns
    -------
    linestring
    """
    if not isinstance(line, LineString) or not line.is_valid or (front_prolong_len == end_prolong_len == 0):
        return line

    coords: List[CoordType] = list(line.coords)

    if len(coords) < 2:
        return line

    def find_diff_coord_from(given_coord: CoordType, given_coords: List[CoordType], start_index: int, step: int):
        assert step != 0, "step cannot equal to 0"

        while 0 <= start_index < len(given_coords):
            if given_coord != given_coords[start_index]:
                return given_coords[start_index]
            start_index += step

        return None

    coord_1 = find_diff_coord_from(coords[0], coords, 1, 1)
    coord_n2 = find_diff_coord_from(coords[-1], coords, len(coords) - 2, -1)
    if not (coord_1 and coord_n2):
        return line

    front_vec: Vector = Vector.from_origin_to_target(coord_1, coords[0]).unit(front_prolong_len)
    end_vec: Vector = Vector.from_origin_to_target(coord_n2, coords[-1]).unit(end_prolong_len)

    new_front: CoordType = front_vec.apply_coord(coords[0])
    new_end: CoordType = end_vec.apply_coord(coords[-1])

    return LineString([new_front, *coords[1: -1], new_end])


class Prolong:
    """
    Prolong mode for linestring
    """

    def __init__(self, line: LineString, absolute: bool = True):
        self._line = line
        self._absolute = absolute

    def from_end(self, end: Union[CoordType, Point], dist: Num):
        coords = list(self._line.coords)
        start_pt: Point = Point(coords[0])
        end_pt: Point = Point(coords[-1])
        given_end_pt = Point(end)

        if not self._absolute:
            dist = dist * self._line.length

        if start_pt.distance(given_end_pt) < end_pt.distance(given_end_pt):
            return self.from_head(dist)

        return self.from_tail(dist)

    def from_ends(self, dist: Num):
        if not self._absolute:
            dist = dist * self._line.length

        return prolong(self._line, front_prolong_len=float(dist), end_prolong_len=float(dist))

    def from_head(self, dist: Num):
        if not self._absolute:
            dist = dist * self._line.length

        return prolong(self._line, front_prolong_len=float(dist))

    def from_tail(self, dist: Num):
        if not self._absolute:
            dist = dist * self._line.length

        return prolong(self._line, end_prolong_len=float(dist))
