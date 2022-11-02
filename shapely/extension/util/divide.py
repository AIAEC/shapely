from collections.abc import Sequence
from copy import deepcopy
from queue import Queue
from typing import Union, List, Dict

from shapely.extension.geometry.straight_segment import StraightSegment

from shapely.extension.constant import MATH_EPS, SAFE_COUNT
from shapely.extension.util.func_util import lconcat, lmap
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import LineString, MultiLineString, Point, Polygon, MultiPolygon, MultiPoint
from shapely.geometry.base import BaseGeometry, CAP_STYLE, JOIN_STYLE
from shapely.ops import split, unary_union, substring, linemerge

__all__ = ['divide']


def _line_divided_by_points(line: Union[LineString, MultiLineString],
                            points: Union[Point, Sequence[Point], MultiPoint],
                            dist_tol: float = MATH_EPS) -> List[LineString]:
    from shapely.extension.util.flatten import flatten

    def divide_single_line(line_, points_):
        points_ = flatten(points_).to_list()

        marks: List[float] = []
        for point in filter(lambda pt: pt.distance(line_) <= dist_tol, points_):
            project_mark = line_.project(point)
            if dist_tol <= project_mark <= line_.length - dist_tol:
                marks.append(project_mark)

        marks = [0, *sorted(marks), line_.length]
        substrings = [substring(line_, mark0, mark1) for mark0, mark1 in win_slice(marks, win_size=2)]

        return (unary_union(substrings)
                .ext.flatten(LineString)
                .to_list())

    lines = line.ext.flatten(LineString).to_list()
    return lconcat([divide_single_line(line, points) for line in lines])


def _delete_segments(segments: List[LineString],
                     rings_of_poly: BaseGeometry,
                     dist_tol: float = MATH_EPS) -> List[LineString]:
    end_to_lines: Dict[Point, List[LineString]] = {}
    for seg in segments:
        for coord in seg.coords:
            end_to_lines.setdefault(Point(coord), []).append(seg)

    single_end_queue: Queue[Point] = Queue(maxsize=0)
    for pt in end_to_lines.keys():
        if len(end_to_lines.get(pt)) < 2 and pt.distance(rings_of_poly) > dist_tol:
            single_end_queue.put(pt)

    safe_count = SAFE_COUNT
    while not single_end_queue.empty():
        safe_count -= 1
        single_end = single_end_queue.get()
        if not (seg := deepcopy(end_to_lines.get(single_end))):
            continue
        pts = [Point(coord) for coord in seg[0].coords]
        for pt in pts:
            try:
                end_to_lines.get(pt).remove(seg[0])
                if len(end_to_lines.get(pt)) == 0:
                    end_to_lines.pop(single_end)
                elif len(end_to_lines.get(pt)) == 1 and pt.distance(rings_of_poly) > dist_tol:
                    single_end_queue.put(pt)
            except Exception:
                continue

    return list(set(lconcat(list(end_to_lines.values()))))


def _split_polygon_boundary(polygon: Polygon,
                            divider: List[LineString],
                            dist_tol: float = MATH_EPS) -> Polygon:
    polygon = polygon.simplify(dist_tol)
    original_rings_of_poly = polygon.exterior.ext.decompose(StraightSegment).to_list()
    remained_divider = unary_union(lmap(lambda l: l.ext.prolong().from_ends(dist_tol).difference(polygon), divider))
    new_rings_of_poly: List[LineString] = []
    for seg in original_rings_of_poly:
        new_rings_of_poly.extend(split(seg, remained_divider).ext.decompose(LineString).to_list())
    return Polygon(shell=linemerge(new_rings_of_poly))


def _divide_polygon_by_multilinestring(polygon: Polygon,
                                       divider: MultiLineString,
                                       dist_tol: float = MATH_EPS) -> List[Polygon]:
    from shapely.extension.util.flatten import flatten

    lines = divider.ext.flatten(LineString).to_list()
    rings_of_poly = unary_union(polygon.ext.decompose(LineString).to_list())
    cross_points: List[Point] = []
    for i in range(len(lines)):
        cross_points.extend(flatten(unary_union(lines[:i] + [rings_of_poly]).intersection(lines[i]), Point).to_list())

    segments = _line_divided_by_points(divider, cross_points, dist_tol)
    divider = _delete_segments(segments, rings_of_poly, dist_tol)
    if not divider:
        return [polygon]

    divider_shape = unary_union(divider).buffer(dist_tol / 10, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre)
    divided_polys = polygon.difference(divider_shape).ext.flatten(Polygon).to_list()
    return lmap(lambda poly: _split_polygon_boundary(poly, divider, dist_tol*10), divided_polys)


def divide(geom_or_geoms: Union[BaseGeometry, List[BaseGeometry]],
           divider: Union[LineString, MultiLineString, BaseGeometry],
           dist_tol: float = MATH_EPS) -> List:
    """
    divide the geom_or_geoms by divider(only linestring(s) or multi-linestring)
    Parameters
    ----------
    geom_or_geoms: geometry(s)
    divider: only linestring(s) or multi-linestring
    dist_tol: max distance for divider's point snapping to geom_or_geoms' boundary

    Returns
    -------
    list of geometry instances
    """
    if not isinstance(divider, (LineString, MultiLineString)):
        return unary_union(geom_or_geoms).difference(divider).ext.flatten().to_list()

    from shapely.extension.util.flatten import flatten
    geom_dict: Dict[type, List[BaseGeometry]] = flatten(geom_or_geoms).group_by(type).to_dict()

    points = geom_dict.get(Point, [])
    lines = geom_dict.get(LineString, [])
    polygons = geom_dict.get(Polygon, [])

    if isinstance(divider, LineString):
        if polygons:
            polygons = split(MultiPolygon(polygons), divider).ext.flatten(Polygon).to_list()
    else:  # MultiLineString
        # the shapely split method can only handle linestring as splitter, and they do so for reason as that,
        # when splitting by a multi-linestring, the order of splitting by each linestring affects the result
        # dramatically, since split won't cut off if the splitter didn't go across the target.
        # for instance, if we split the polygon using line2 first, then line2 split nothing, and result has 2 pieces
        # if we split using line1 first, then the result has 3 pieces
        #    1
        # ┌──┼───────┐
        # │  │       │
        # │ ─┼───────┼─2
        # │  │       │
        # └──┼───────┘

        divided_polys: List[Polygon] = []
        for polygon in polygons:
            divided_polys.extend(_divide_polygon_by_multilinestring(polygon, divider, dist_tol))

        polygons = divided_polys

    if len(lines) > 0:
        lines = split(MultiLineString(lines), divider).ext.flatten(LineString).to_list()

    return polygons + lines + points
