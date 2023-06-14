from typing import List, Literal


from shapely.extension.model.vector import Vector
from shapely.geometry import Point


def get_points(exter_coords_list: List[List], inter_coords_list: List[List],
               boundary_type: Literal["exterior", "interiors", "both"] = "exterior") -> List[Point]:
    """
    if a polygon in counter-clockwise direction, it will return convex_points in boundary_type
    if a polygon in clockwise direction, it will return concave points in boundary_type
    Args:
        exter_coords_list: polygon exterior coords list
        inter_coords_list: polygon interiors coords list
        boundary_type: which polygon boundary type you want to get points

    Returns:
        the convex points or concave points you want in appointed boundary

    """

    points: List[Point] = []
    if boundary_type == "exterior":
        coords_list = exter_coords_list
    elif boundary_type == "interiors":
        coords_list = inter_coords_list
    else:
        coords_list = exter_coords_list + inter_coords_list
    for coords in coords_list:
        if coords[-1] == coords[0]:
            coords.pop()

        for i, coord in enumerate(coords):
            prev = coords[i - 1]
            next_ = coords[(i + 1) % len(coords)]
            if Vector.from_origin_to_target(prev, coord).cross_prod(Vector.from_origin_to_target(coord, next_)) > 0:
                points.append(Point(coord))

    return points
