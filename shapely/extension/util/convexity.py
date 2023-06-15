from typing import List, Literal

from pycore_util.func.func_util import lflatten

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


def convex_points_in_bounds(poly: Polygon, boundary_type: Literal["exterior", "interiors", "both"] = "both",
                            counter_clockwise: bool = True) -> List[Point]:
    """
    return convex points in appointed boundary
    note: if counter_clockwise is false, you will get concave points

    Parameters
    ----------
    poly
    boundary_type: get convex points from exterior polygon or interiors polygon or both
    counter_clockwise: ccw flag, if it is false, we will make exterior cw and interiors ccw.

    Returns
    -------
    convex points
    """
    if poly.is_empty or not poly.is_valid:
        return []
    # make the coords in counter-clockwise direction
    poly = ccw(poly.simplify(0))
    ccw_direction = 1 if counter_clockwise else -1

    exterior_coords_list = list(poly.exterior.coords)[::ccw_direction]
    if boundary_type == "exterior":
        points = lmap(Point, convex_coords(exterior_coords_list))
    elif boundary_type == "interiors":

        points = lflatten(
            [lmap(Point, (convex_coords(list(interior.coords)[::ccw_direction]))) for interior in poly.interiors])
    elif boundary_type == "both":

        points = lmap(Point, convex_coords(exterior_coords_list)) + lflatten(
            [lmap(Point, convex_coords(list(interior.coords)[::ccw_direction])) for interior in poly.interiors])
    else:
        raise ValueError("Invalid Boundary Type")

    return points
