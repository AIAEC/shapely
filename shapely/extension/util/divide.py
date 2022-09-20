from collections.abc import Sequence
from typing import Union, List, Dict

from functional import seq

from shapely.extension.constant import MATH_EPS
from shapely.extension.typing import Num
from shapely.extension.util.flatten import flatten
from shapely.extension.util.func_util import lfilter, lconcat
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import LineString, MultiLineString, Point, Polygon, MultiPolygon, MultiPoint
from shapely.geometry.base import BaseGeometry, CAP_STYLE, JOIN_STYLE
from shapely.ops import split, unary_union, substring

__all__ = ['divide']


def _line_divided_by_points(line: Union[LineString, MultiLineString],
                            points: Union[Point, Sequence[Point], MultiPoint],
                            dist_tol: Num = MATH_EPS) -> List[LineString]:
    def divide_single_line(line_, points_):
        points_ = flatten(points_, Point).to_list()

        marks: List[float] = []
        for point in filter(lambda pt: pt.distance(line_) <= dist_tol, points_):
            project_mark = line_.project(point)
            if dist_tol <= project_mark <= line_.length - dist_tol:
                marks.append(project_mark)

        marks = [0, *sorted(marks), line_.length]
        return flatten([substring(line_, mark0, mark1) for mark0, mark1 in win_slice(marks, win_size=2)],
                       LineString).to_list()

    lines = flatten(line, LineString).to_list()
    return lconcat([divide_single_line(line, points) for line in lines])


def _divide_polygon_by_multilinestring(polygon: Polygon,
                                       divider: MultiLineString,
                                       dist_tol: Num = MATH_EPS) -> List[Polygon]:
    lines = flatten(divider, LineString).to_list()
    cross_points: List[Point] = []
    for i in range(1, len(lines)):
        cross_points.extend(flatten(unary_union(lines[:i]).intersection(lines[i]), Point).to_list())

    rings_of_poly = unary_union(polygon.ext.decompose(LineString).to_list())
    segments = _line_divided_by_points(divider, cross_points, dist_tol)
    deleting_segments = lfilter(lambda seg: seg.distance(rings_of_poly) > dist_tol, segments)
    divider = divider.difference(
        unary_union(deleting_segments).buffer(dist_tol / 10, cap_style=CAP_STYLE.flat, join_style=JOIN_STYLE.mitre))
    divider = divider.buffer(dist_tol, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre)
    return flatten(polygon.difference(divider), Polygon).to_list()


def divide(geom_or_geoms: Union[BaseGeometry, List[BaseGeometry]],
           divider: Union[LineString, MultiLineString, BaseGeometry],
           dist_tol: Num = MATH_EPS) -> List[BaseGeometry]:
    if not isinstance(divider, (LineString, MultiLineString)):
        return flatten(unary_union(geom_or_geoms).to_list().difference(divider))

    geom_dict: Dict[type, List[BaseGeometry]] = seq(flatten(geom_or_geoms).to_list()).group_by(type).to_dict()

    points = geom_dict.get(Point, [])
    lines = geom_dict.get(LineString, [])
    polygons = geom_dict.get(Polygon, [])

    if isinstance(divider, LineString):
        if polygons:
            polygons = flatten(split(MultiPolygon(polygons), divider), Polygon).to_list()
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
        lines = flatten(split(MultiLineString(lines), divider), LineString).to_list()

    return polygons + lines + points
