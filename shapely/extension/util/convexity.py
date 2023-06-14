from typing import List, Literal

from shapely.extension.model.vector import Vector
from shapely.extension.typing import CoordType
from shapely.geometry import Point


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


def transform_coords_to_points(coords: List[CoordType]) -> List[Point]:
    points: List[Point] = []
    for coord in coords:
        points.append(Point(coord))

    return points
