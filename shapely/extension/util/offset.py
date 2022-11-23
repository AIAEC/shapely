from operator import attrgetter
from typing import List, Set, Union

from functional import seq
from numpy import argmin

from shapely.extension.model.coord import Coord
from shapely.extension.typing import CoordType
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lmap
from shapely.geometry import LineString, JOIN_STYLE, Point, LinearRing, Polygon, MultiLineString
from shapely.geos import geos_version_string
from shapely.ops import unary_union

__all__ = ['offset']


def reverse_line(line: Union[LineString, MultiLineString]) -> Union[LineString, MultiLineString]:
    """
    reverse the order of the coordinates of linestring or multi-linestring
    Parameters
    ----------
    line: linestring or multi-linestring

    Returns
    -------
    linestring or multi-linestring
    """
    if isinstance(line, LineString):
        return LineString(list(line.coords)[::-1])
    return type(line)([reverse_line(l) for l in line.geoms])


def self_intersection(line: LineString) -> List[Point]:
    """
    return the list of self-intersection point of given linestring
    Parameters
    ----------
    line: linestring

    Returns
    -------
    list of points
    """
    if not isinstance(line, LineString):
        raise TypeError(f'expect line of type LineString, given {type(line)}')

    intersections: Set[CoordType] = set()
    coords: List[CoordType] = list(line.coords)
    for i in range(2, len(coords) - 1):
        pre_seg = LineString(coords[:i])
        next_seg = LineString(coords[i:])
        if intersection := pre_seg.intersection(next_seg):
            for point in flatten(intersection, Point).to_list():
                intersections.add(point.coords[0])

    return lmap(Point, intersections)


def offset(line: LineString,
           dist: float,
           side: str = 'left',
           invert_coords: bool = False,
           join_style: int = JOIN_STYLE.mitre) -> LineString:
    """
    return the offset linestring if offset success, otherwise return empty linestring
    Parameters
    ----------
    line: linestring been offset
    dist: offset distance
    side: 'left' or 'right', with ccw order to be left
    invert_coords: whether invert the order of coordinates of return linestring
    join_style: join style of offset, mitre as default

    Returns
    -------
    linestring
    """
    if dist == 0 or line.is_empty:
        if invert_coords:
            return reverse_line(line)
        return line

    offset_to_right_side: bool = dist > 0 and side.lower() == 'right' or dist < 0 and side.lower() == 'left'
    self_intersected_pts: List[Point] = self_intersection(line)
    is_linearRing = isinstance(line, LinearRing)
    is_loop_linestring = isinstance(line, LineString) and line.coords[0] == line.coords[-1]
    # simple ring-like linestring with only head connected to tail
    is_simple_ring: bool = (len(self_intersected_pts) == 1
                            and (is_linearRing or is_loop_linestring))

    #######################################
    # if line is a simple ring, with and only with head and tail connected to each other
    # use native buffer and pick the exterior or interior of the resulting polygon for its offset
    if is_simple_ring:
        ring_poly = max(flatten(line.buffer(distance=abs(dist), join_style=join_style), Polygon).to_list(),
                        key=attrgetter('area'), default=Polygon())
        pick_exterior: bool = LinearRing(line).is_ccw ^ offset_to_right_side
        if pick_exterior:
            offset_line = reverse_line(ring_poly.exterior)
            if invert_coords:
                return reverse_line(offset_line)
            return offset_line
        else:  # pick the longest interior
            return max(ring_poly.interiors, key=attrgetter('length'), default=LineString())

    #######################################
    # if line is not a simple ring, then it could be
    # 1. a linestring (whether self-intersected or not)
    # 2. a twisted ring (with more than 1 self-intersection points)
    # for the #1 case, we simply try to use the native parallel offset
    # thus if the native parallel_offset gives a linestring, then that's the answer
    def parallel_offset_with_coord_order_kept(line, dist, side, join_style):
        offset_line = line.parallel_offset(distance=dist, side=side, join_style=join_style)
        if not offset_line or not isinstance(offset_line, LineString):
            return offset_line

        # try to check the coordinates order
        # for GEOS <= 3.9 on Darwin(macos), the parallel_offset might reverse the order of coordinates of result line
        # for GEOS >= 3.10 on Darwin(macos), the parallel_offset might not reverse the coord order of the result
        # for GEOS on linux, the behaviour of parallel_offset is undetermined
        # in order to handle the coord reverse situation, we calculate the interpolated points distance between
        # origin line and offset line as the cost of offset line. we compare cost of offset line and cost of its
        # reverse and choose to pick the one with less cost
        origin_points = line.ext.interpolate([i/10 for i in range(11)], absolute=False)
        offset_points = offset_line.ext.interpolate([i/10 for i in range(11)], absolute=False)
        offset_line_cost = sum(pt0.distance(pt1) for pt0, pt1 in zip(origin_points, offset_points))
        reverse_offset_line_cost = sum(pt0.distance(pt1) for pt0, pt1 in zip(origin_points, offset_points[::-1]))

        if reverse_offset_line_cost < offset_line_cost:
            offset_line = reverse_line(offset_line)
        return offset_line.simplify(0)

    # native parallel_offset have several side effects
    # the first is: it will reverse coordinates order WHEN offset to RIGHT side!!
    line = line.simplify(0)
    offset_line = parallel_offset_with_coord_order_kept(line=line, dist=dist, side=side, join_style=join_style)
    if isinstance(offset_line, LineString):
        if isinstance(line, LinearRing) and offset_line.coords[0] != offset_line.coords[-1]:
            # if given line is a linearRing, make its offset's head connect to tail
            coords = list(offset_line.coords)
            coords.append(coords[0])
            offset_line = LineString(coords)

        if invert_coords:
            return reverse_line(offset_line)

        return offset_line

    #######################################
    # if line is not a simple ring, then it could be
    # 1. a linestring (whether self-intersected or not)
    # 2. a twisted ring (with more than 1 self-intersection points)
    # for the #2 case, we cut the line at the self-intersection points and offset each segment, then try to union them
    # into linestring
    if self_intersected_pts:
        pieces = flatten(line.difference(unary_union(self_intersected_pts)), LineString).to_list()
        offset_pieces: List[LineString] = []
        for piece in pieces:
            offset_piece = offset(line=piece,
                                  dist=dist,
                                  side=side,
                                  invert_coords=invert_coords,
                                  join_style=join_style)
            if offset_piece.coords[0] == offset_piece.coords[-1]:
                # piece is a ring, according to side effect of parallel_offset, we should reorder the coordinates
                # so that offset pieces might be connected smoothly
                if not offset_pieces:
                    offset_pieces.append(offset_piece)
                    continue

                # native parallel_offset have several side effects
                # the second is: when given line is ring-like, the order of coordinates might change,
                # thus starts from different coordinate
                last_piece_end = offset_pieces[-1].coords[-1]
                coords = list(offset_piece.coords)[:-1]
                coord_dist_to_last_piece_end = lmap(lambda crd: Coord.dist(crd, last_piece_end), coords)
                new_start_idx = argmin(coord_dist_to_last_piece_end)
                modified_coords = coords[new_start_idx:] + coords[:new_start_idx + 1]  # try to make a new ring
                offset_pieces.append(LineString(modified_coords))
            else:
                offset_pieces.append(offset_piece)

        return LineString(seq(offset_pieces).flat_map(lambda line: list(line.coords)).to_list())

    # if it appeared non-self-intersection but still given a MultiLineString as offset
    # we do a default process: pick the longest offset line as the result
    return max(flatten(offset_line, LineString).to_list(), key=attrgetter('length'), default=LineString())
