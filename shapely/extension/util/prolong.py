from typing import Union, List, Sequence, Optional, Literal

from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.geometry import Point, LineString, MultiPoint
from shapely.ops import substring
from shapely.geometry.base import BaseGeometry
from shapely.extension.util.decompose import decompose
from shapely.extension.geometry.straight_segment import StraightSegment
import numpy as np


def _find_first_diff_coord_from(target_coord: CoordType, coords: List[CoordType], start_index: int, step: int):
    assert step != 0, "step cannot equal to 0"

    while 0 <= start_index < len(coords):
        if target_coord != coords[start_index]:
            return coords[start_index]
        start_index += step

    return None


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

    if len(coords) < 2:  # invalid or empty LineString
        return line

    coord_1 = _find_first_diff_coord_from(coords[0], coords, 1, 1)
    coord_n2 = _find_first_diff_coord_from(coords[-1], coords, len(coords) - 2, -1)
    if not (coord_1 and coord_n2):
        return line

    if front_prolong_len > 0:
        front_vec: Vector = Vector.from_origin_to_target(coord_1, coords[0]).unit(front_prolong_len)
        new_front: CoordType = front_vec.apply_coord(coords[0])
        start_dist = 0  # start from new_front point
    else:
        new_front = coords[0]
        start_dist = abs(front_prolong_len)  # if front_prolong_len is "-n", start dist is "n"

    if end_prolong_len > 0:
        end_vec: Vector = Vector.from_origin_to_target(coord_n2, coords[-1]).unit(end_prolong_len)
        new_end: CoordType = end_vec.apply_coord(coords[-1])
        dist_to_end = 0  # end to new_end point
    else:
        new_end = coords[-1]
        dist_to_end = abs(end_prolong_len)  # if end_prolong_len is "-n", end dist is prolonged.length - n

    prolonged = LineString([new_front, *coords[1: -1], new_end])

    # for negative prolong_len, pick the substring from the prolonged
    return substring(prolonged, start_dist=start_dist, end_dist=prolonged.length - dist_to_end, normalized=False)


def ray_intersection(
    start_point: CoordType,
    end_point: CoordType,
    barriers_geoms: Union[BaseGeometry, Sequence[BaseGeometry]],
) -> Optional[CoordType]:
    """Computes intersection between a ray and barriers.

    Computes the intersections between a ray and all edges of barriers.
    Select the closest intersection to end_point as result.

    Parameters
    ----------
    start_point : CoordType
        the initial point of ray
    end_point : CoordType
        a point on the ray indicating the direction emitted from start_point
    barriers_geoms : Union[BaseGeometry, Sequence[BaseGeometry]]
        the barriers geometries blocking the ray. A point is also considered as a barrier.

    Returns
    -------
    CoordType or None
        A point as the intersection between the ray and barriers, or None if no intersections.

    Raises
    ------
    ValueError
        An error occurred when barriers_geoms can't be composed to edges.
    """

    assert start_point != end_point

    sp: np.ndarray = np.array(start_point)  # start point of ray
    ep: np.ndarray = np.array(end_point)  # end point of ray
    res: Optional[np.ndarray] = None  # nearest intersection point of end point
    dist: np.float64 = np.Inf  # distance between res and end point

    def is_point_on_ray(p: np.ndarray, sp: np.ndarray, ep: np.ndarray) -> bool:
        # p0 = l*(ep0-sp0)+sp0
        # p1 = l*(ep1-sp1)+sp1
        # l1 = (p[0]-sp[0])/(ep[0]-sp[0])
        # l2 = (p[1]-sp[1])/(ep[1]-sp[1])
        if sp[0] == ep[0]:
            return p[0] == sp[0]
        elif sp[1] == ep[1]:
            return p[1] == sp[1]
        l1, l2 = (p - sp) / (ep - sp)
        return np.allclose(l1, l2) and l1 >= 1 and l2 >= 1

    def update(u: np.ndarray, v: np.ndarray) -> None:
        nonlocal res, dist
        alt = np.linalg.norm(v - u)
        if alt < dist:
            dist = alt
            res = v

    for obj in decompose(barriers_geoms, StraightSegment, None, True):
        # compute intersection

        # ray equation:
        # sp---ep--->
        # sp + m*(ep - sp) (m>=1)
        # x = m*(ep0-sp0)+sp0
        # y = m*(ep1-sp1)+sp1

        # line segment equation:
        # u---v
        # u + n*(v-u) (0<=n<=1)
        # x = n*(v0-u0)+u0
        # y = n*(v1-u1)+u1

        # intersection:
        # m*(ep0-sp0)+sp0 = n*(v0-u0)+u0
        # m*(ep1-sp1)+sp1 = n*(v1-u1)+u1
        # m*(ep0-sp0)+n*(u0-v0) = u0-sp0
        # m*(ep1-sp1)+n*(u1-v1) = u1-sp1
        # a = [ep0-sp0 u0-v0] b = [u0-sp0] x = [m]
        #     [ep1-sp1 u1-v1]     [u1-sp1]     [n]

        # if line segment u-v is parallel to ray sp-ep or barrier is point, determine if it is on the ray
        # else solve linear matrix equation a*x = b where x = [m n]
        # compute intersection p using m and n, then compute distance between p and end_point, update shortest point

        if isinstance(obj, StraightSegment):
            u = np.array(obj.coords[0])
            v = np.array(obj.coords[1])
            a = np.column_stack((ep - sp, u - v))
            if np.allclose(np.linalg.det(a), 0):
                if is_point_on_ray(u, sp, ep):
                    update(ep, u)
                if is_point_on_ray(v, sp, ep):
                    update(ep, v)
            else:
                b = u - sp
                m, n = np.linalg.solve(a, b)
                if m >= 1 and n >= 0 and n <= 1:
                    p = n * (v - u) + u
                    update(ep, p)
        elif isinstance(obj, MultiPoint):
            for p in obj.geoms:
                p = np.array(p)
                if is_point_on_ray(p, sp, ep):
                    update(ep, p)
        elif isinstance(obj, Point):
            p = np.array(obj)
            if is_point_on_ray(p, sp, ep):
                update(ep, p)
        else:
            raise ValueError("Can't decompose geometries")

    return tuple(res) if isinstance(res, np.ndarray) else None


class Prolong:
    """
    Prolong mode for linestring
    """

    def __init__(self, line: LineString, absolute: bool = True):
        self._line = line
        self._absolute = absolute

    def from_end(self, end: Union[CoordType, Point], dist: float):
        coords = list(self._line.coords)
        start_pt: Point = Point(coords[0])
        end_pt: Point = Point(coords[-1])
        given_end_pt = Point(end)

        if not self._absolute:
            dist = dist * self._line.length

        if start_pt.distance(given_end_pt) < end_pt.distance(given_end_pt):
            return self.from_head(dist)

        return self.from_tail(dist)

    def from_ends(self, dist: float):
        if not self._absolute:
            dist = dist * self._line.length

        return prolong(self._line, front_prolong_len=float(dist), end_prolong_len=float(dist))

    def from_head(self, dist: float):
        if not self._absolute:
            dist = dist * self._line.length

        return prolong(self._line, front_prolong_len=float(dist))

    def from_tail(self, dist: float):
        if not self._absolute:
            dist = dist * self._line.length

        return prolong(self._line, end_prolong_len=float(dist))

    def _util_touching_from(
        self,
        position: Literal["head", "tail"],
        geoms: Union[BaseGeometry, Sequence[BaseGeometry]],
        ret_none_if_fail: bool = False,
    ) -> Optional[LineString]:
        """Prolong from head or tail direction until reach a barrier.

        Parameters
        ----------
        position : Literal["head", "tail"]
            indicate direction from head or tail
        geoms : Union[BaseGeometry, Sequence[BaseGeometry]]
            barriers or list of barriers
        ret_none_if_fail : bool
            if True, return None when no intersection found, else return original LineString. The default is False.

        Returns
        -------
        Optional[LineString]
            A new prolonged LineString
        """
        coords: List[CoordType] = list(self._line.coords)
        start_point: Optional[CoordType] = None
        end_point: Optional[CoordType] = None
        intersect_point: Optional[CoordType] = None

        if position == "head":
            start_point = _find_first_diff_coord_from(coords[0], coords, 1, 1)
            end_point = coords[0]
        elif position == "tail":
            start_point = _find_first_diff_coord_from(coords[-1], coords, len(coords) - 2, -1)
            end_point = coords[-1]

        if start_point and end_point and start_point != end_point:
            intersect_point = ray_intersection(start_point, end_point, geoms)

        if intersect_point:
            if intersect_point == end_point:
                return LineString(coords)
            if position == "head":
                return LineString([intersect_point] + coords)
            if position == "tail":
                return LineString(coords + [intersect_point])

        if ret_none_if_fail:
            return None
        else:
            return LineString(coords)

    def from_head_util_touching(
        self,
        geoms: Union[BaseGeometry, Sequence[BaseGeometry]],
        ret_none_if_fail: bool = False,
    ) -> Optional[LineString]:
        return self._util_touching_from("head", geoms, ret_none_if_fail)

    def from_tail_util_touching(
        self,
        geoms: Union[BaseGeometry, Sequence[BaseGeometry]],
        ret_none_if_fail: bool = False,
    ) -> Optional[LineString]:
        return self._util_touching_from("tail", geoms, ret_none_if_fail)
