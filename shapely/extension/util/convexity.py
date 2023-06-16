from typing import List, Literal

from toolz import curry

from shapely.extension.functional import seq
from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.extension.util.ccw import ccw
from shapely.extension.util.func_util import lmap
from shapely.geometry import Point, Polygon


def convex_coords(ccw_coords: List[CoordType]) -> List[CoordType]:
    """
    find convex coords in ccw_coords

    Parameters
    ----------
    ccw_coords: coords list in counter-clockwise direction

    Returns
    -------
    convex coords
    """
    coords = []

    if ccw_coords[-1] == ccw_coords[0]:
        ccw_coords.pop()

    for i, coord in enumerate(ccw_coords):
        prev = ccw_coords[i - 1]
        next_ = ccw_coords[(i + 1) % len(ccw_coords)]
        if Vector.from_origin_to_target(prev, coord).cross_prod(Vector.from_origin_to_target(coord, next_)) > 0:
            coords.append(coord)

    return coords


@curry
def corner_points(poly: Polygon,
                  on_boundary: Literal["exterior", "interiors", "both"] = "both",
                  convex_corner: bool = True) -> List[Point]:
    """
    decompose a polygon into points and pick the convex or concave ones.

    Parameters
    ----------
    poly: polygon instance
    on_boundary: get convex points from exterior polygon or interiors polygon or both
    convex_corner: if true, return convex points, else return concave points

    Returns
    -------
    points according to given convex_corner parameter
    """
    if on_boundary not in ["exterior", "interiors", "both"]:
        raise ValueError("Invalid Boundary Type")

    if poly.is_empty or not poly.is_valid:
        return []

    # make the coords in counter-clockwise direction
    poly = ccw(poly.simplify(0))
    ccw_direction = 1 if convex_corner else -1

    exterior_coords_list = list(poly.exterior.coords)[::ccw_direction]
    points: List[Point] = []

    if on_boundary in ["exterior", "both"]:
        points.extend(lmap(Point, convex_coords(exterior_coords_list)))

    if on_boundary in ["interiors", "both"]:
        points.extend(seq(list(poly.interiors))
                      .map(lambda interior: list(interior.coords)[::ccw_direction])
                      .flat_map(convex_coords)
                      .map(Point)
                      .list())

    return points
